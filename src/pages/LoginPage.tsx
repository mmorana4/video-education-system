import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const LoginPage = (): JSX.Element => {
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLogin = () => {
    login(); // Marca al usuario como autenticado
    navigate('/dashboard'); // Redirige al dashboard
  };

  return (
    <div className="flex flex-col items-center justify-center h-screen">
      <h2 className="text-2xl font-bold mb-4">Iniciar sesión</h2>
      <button
        onClick={handleLogin}
        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
      >
        Entrar
      </button>
    </div>
  );
};

export default LoginPage;

