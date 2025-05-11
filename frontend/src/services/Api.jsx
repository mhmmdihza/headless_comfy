import { useCallback } from 'react';
import { useAuth } from './AuthContext';

const API_BASE_URL = import.meta.env.VITE_API_URL;

export function useApi() {
  const { accessToken } = useAuth();

  const uploadFile = useCallback(async (formData) => {
    return await fetch(`${API_BASE_URL}/generate`, {
      method: 'POST',
      headers: {
        ...(accessToken && { Authorization: `Bearer ${accessToken}` }),
      },
      body: formData,
    });
  }, [accessToken]);

  const getQueues = useCallback(async () => {
    const res = await fetch(`${API_BASE_URL}/queues`, {
      method: 'GET',
      headers: {
        ...(accessToken && { Authorization: `Bearer ${accessToken}` }),
      },
    });

    if (res.ok) {
      return await res.json();
    } else {
      console.error('Failed to fetch queues:', res.statusText);
      return [];
    }
  }, [accessToken]);

  const getStatus = useCallback(async (jobId) => {
    const res = await fetch(`${API_BASE_URL}/status/${jobId}`, {
      method: 'GET',
      headers: {
        ...(accessToken && { Authorization: `Bearer ${accessToken}` }),
      },
    });
  
    const metadata = res.headers.get("X-Image-Metadata");
    const status = metadata ? JSON.parse(metadata).status : "UNKNOWN";
  
    if (res.ok) {
      const contentType = res.headers.get("Content-Type");
      
      if (contentType && contentType.startsWith("image/")) {
        const blob = await res.blob();
        const imageUrl = URL.createObjectURL(blob);
        return { status, imageUrl };
      } else {
        return { status, imageUrl: null };
      }
    } else {
      throw new Error("Failed to fetch status");
    }
  }, [accessToken]);

  const subscribeToQueueStatus = useCallback((id, onMessage) => {
    const ws = new WebSocket(`${API_BASE_URL.replace(/^http(s?)/, 'ws$1')}/ws/status?id=${id}&token=${accessToken}`);
  
    ws.onmessage = (event) => {
      const status = event.data;
      onMessage(status);
  
      if (status === 'COMPLETED' || status === 'FAILED') {
        ws.close();
      }
    };
  
    ws.onerror = (err) => {
      console.error(`WebSocket error for ID ${id}:`, err);
    };
  
    return () => {
      ws.close(); // return cleanup function
    };
  }, [accessToken]);

  return { uploadFile, getQueues, getStatus, subscribeToQueueStatus };
}
