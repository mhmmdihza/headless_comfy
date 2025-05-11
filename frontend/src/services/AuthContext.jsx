import { createContext, useContext, useEffect, useState } from 'react';
import { supabase } from '../supabaseClient';

// Create AuthContext
const AuthContext = createContext();

// Custom hook to use the AuthContext
export const useAuth = () => {
  return useContext(AuthContext);
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [accessToken, setAccessToken] = useState(null);


  useEffect(() => {
    // Check existing session on mount
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null);
    });

    // Listen for auth changes (e.g., login/logout)
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (event, session) => {
        setUser(session?.user ?? null);
        setAccessToken(session?.access_token ?? null);
      }
    );

    return () => {
      // Cleanup on component unmount
      subscription?.unsubscribe();
    };
  }, []);

  return (
    <AuthContext.Provider value={{ user,accessToken, setUser }}>
      {children}
    </AuthContext.Provider>
  );
};
