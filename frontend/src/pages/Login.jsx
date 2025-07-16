import { useState } from 'react'
// import { useNavigate } from 'react-router-dom'
// import jwtDecode from "jwt-decode";
import { default as jwtDecode } from "jwt-decode";
import { useNavigate } from "react-router-dom";

// Read the backend URL you set in Render’s env
const API_URL = import.meta.env.VITE_API_URL || "https://new-dashboard-backend.onrender.com";


export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleLogin = async () => {
    setLoading(true)
    setError('')
    
    try {
      const formData = new URLSearchParams();
      formData.append("username", username);
      formData.append("password", password);
      
      const response = await fetch(`${API_URL}/token`, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: formData
      });

      if (response.ok) {
        const { access_token, role } = await response.json();
        localStorage.setItem('token', access_token);
        localStorage.setItem('role', role);
        navigate('/dashboard');
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Invalid credentials');
      }
    } catch (err) {
      setError('Network error. Please try again.');
      console.error('Login error:', err);
    } finally {
      setLoading(false)
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 px-4">
      <div className="bg-white p-8 rounded-lg shadow-lg w-full max-w-sm">
        <h2 className="text-2xl font-semibold mb-6 text-center">NDA Login</h2>
        {error && <p className="text-red-500 mb-4">{error}</p>}
        <input
          className="w-full p-2 mb-4 border rounded"
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <input
          className="w-full p-2 mb-6 border rounded"
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <button
          onClick={handleLogin}
          disabled={loading}
          className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 transition disabled:opacity-50"
        >
          {loading ? 'Logging in...' : 'Login'}
        </button>
      </div>
    </div>
  )
}
