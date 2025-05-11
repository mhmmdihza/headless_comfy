import { useState } from 'react';
import { useApi } from '../services/Api';

export default function Img2ImgFlux() {
  const [image, setImage] = useState(null);
  const [imagePreviewUrl, setImagePreviewUrl] = useState(null);
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { uploadFile } = useApi();

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        alert('File size exceeds 5MB');
        return;
      }
      setImage(file);
      setImagePreviewUrl(URL.createObjectURL(file));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!image || !prompt) return;

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('image', image);
      formData.append('prompt', prompt);
      const response = await uploadFile(formData);
      if (!response.ok) {
        const errorText = await response.json();
        const errorMessage = errorText?.detail || 'An unknown error occurred';
        throw new Error(`Upload failed: ${errorMessage}`);
      }
      window.location.reload();
    } catch (err) {
      setError(err.message);
      alert(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };
  return (
    <>
      <form
        onSubmit={handleSubmit}
        className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow space-y-4"
      >
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-200">
          Upload Image (Max 5MB)
        </label>
        <input
          type="file"
          accept="image/*"
          onChange={handleImageChange}
          disabled={loading}
          className="w-full border border-gray-300 dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
        />

        {imagePreviewUrl && (
          <div className="mt-2">
            <img
              src={imagePreviewUrl}
              alt="Preview"
              className="rounded shadow-md max-h-64"
            />
          </div>
        )}

        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Enter your prompt"
          disabled={loading}
          className="w-full border border-gray-300 dark:border-gray-600 rounded px-3 py-2 h-24 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
        />

        <button
          type="submit"
          disabled={loading || !image || !prompt}
          className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded transition w-full sm:w-auto"
        >
          {loading ? 'Submitting...' : 'Submit'}
        </button>

        {error && <p className="text-red-600">{error}</p>}
      </form>
    </>
  );
}
