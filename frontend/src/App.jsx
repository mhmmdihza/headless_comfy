import { BrowserRouter as Router } from 'react-router-dom';
import "./index.css";
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import { AuthProvider, useAuth } from './services/AuthContext';

function App() {
  return (
    <Router>

    <AuthProvider>
      <div className="min-h-screen text-gray-900">
        <AuthDisplay />
      </div>
    </AuthProvider>
    </Router>
  );
}

function AuthDisplay() {
  const { user } = useAuth();
  return user ? <Dashboard /> : <Login />;
}

export default App;
