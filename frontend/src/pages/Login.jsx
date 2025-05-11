import { useAuth } from '../services/AuthContext';
import { supabase } from '../supabaseClient';

export default function Login() {
  const { setUser } = useAuth();

  const handleOAuthLogin = async () => {
    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: window.location.origin + '/oauth-callback',
      },
    });

    if (error) alert('OAuth error: ' + error.message);
  };

  return (
    <section className="bg-gray-50 dark:bg-gray-900 min-h-screen flex items-center justify-center">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-md p-8 w-full max-w-sm text-center space-y-6">
        <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
          Welcome to Halu AI
        </h1>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          Sign in to your account
        </h2>
        <button
          onClick={handleOAuthLogin}
          className="w-full flex items-center justify-center gap-3 text-white bg-red-600 hover:bg-red-700 focus:ring-4 focus:outline-none focus:ring-red-300 font-medium rounded-lg text-sm px-5 py-2.5 dark:bg-red-600 dark:hover:bg-red-700 dark:focus:ring-red-800"
        >
          <svg className="w-5 h-5" viewBox="0 0 533.5 544.3" xmlns="http://www.w3.org/2000/svg">
            <path fill="#4285F4" d="M533.5 278.4c0-17.7-1.6-35-4.6-51.6H272v97.7h146.9c-6.4 34.5-25.5 63.8-54.2 83.3v68.6h87.6c51.3-47.2 81.2-116.7 81.2-198z"/>
            <path fill="#34A853" d="M272 544.3c73.5 0 135-24.5 180-66.6l-87.6-68.6c-24.2 16.2-55.1 25.8-92.3 25.8-70.9 0-131-47.9-152.4-112.4H29.6v70.5c44.9 89.7 137.4 151.3 242.4 151.3z"/>
            <path fill="#FBBC05" d="M119.6 322.5c-10.4-30.5-10.4-63.9 0-94.4V157.6H29.6c-39.8 79.4-39.8 172.3 0 251.7l90-70.5z"/>
            <path fill="#EA4335" d="M272 107.5c39.8 0 75.6 13.7 103.9 40.6l77.8-77.8C407 24.5 345.5 0 272 0 167 0 74.5 61.6 29.6 151.3l90 70.5C141 155.4 201.1 107.5 272 107.5z"/>
          </svg>
          Sign in with Google
        </button>
      </div>
    </section>
  );
}
