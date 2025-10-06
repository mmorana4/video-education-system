import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { FiUser, FiLock } from 'react-icons/fi';

const LoginPage = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleLogin = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/token/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (response.ok) {
        login(data.access);
        localStorage.setItem('access', data.access);   // ✅ Clave para que VideosPage funcione
        localStorage.setItem('refresh', data.refresh);
        console.log('Login exitoso:', data.access);
        navigate('/dashboard');
      } else {
        setError(data.detail || 'Credenciales incorrectas');
      }
    } catch (err) {
      setError('Error de conexión con el servidor');
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-200">
      <div className="w-full max-w-md p-8 bg-white border border-gray-300 rounded-lg shadow-md">
        {/* Título */}
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold text-gray-800">Login</h1>
        </div>

        {/* Formulario */}
        <form onSubmit={handleLogin} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Nombre de usuario</label>
            <div className="relative">
              <FiUser className="absolute left-3 top-3 text-gray-400" />
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-400 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Contraseña</label>
            <div className="relative">
              <FiLock className="absolute left-3 top-3 text-gray-400" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-400 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                required
              />
            </div>
          </div>

          {/* Recordarme */}
          <div className="flex items-center">
            <input type="checkbox" id="remember" className="mr-2" />
            <label htmlFor="remember" className="text-sm text-gray-600">Recordarme</label>
          </div>

          {/* Botón */}
          <button
            type="submit"
            className="w-full mt-4 py-2 bg-blue-600 text-white font-semibold rounded hover:bg-blue-700 transition duration-200"
          >
            Acceder
          </button>
        </form>

        {/* Error */}
        {error && <p className="text-red-600 mt-4 text-center">{error}</p>}
      </div>
    </div>
  );
};

export default LoginPage;
