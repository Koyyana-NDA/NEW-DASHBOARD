import { useState } from 'react'
// import { useNavigate } from 'react-router-dom'
import jwtDecode from "jwt-decode";
import { useNavigate } from "react-router-dom";


export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const handleLogin = async () => {
    const formData = new URLSearchParams();
    formData.append("username", username);
    formData.append("password", password);
    const response = await fetch("http://127.0.0.1:8000/token", {
      method: "POST",
      headers: {"Content-Type": "application/x-www-form-urlencoded"},
      body: formData
    });
    

    if (response.ok) {
        const { access_token, role } = await response.json();
        localStorage.setItem('token', access_token);
        localStorage.setItem('role', role);
        navigate('/dashboard');
    } else {
        setError('Invalid credentials');
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
          className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 transition"
        >
          Login
        </button>
      </div>
    </div>
  )
}
