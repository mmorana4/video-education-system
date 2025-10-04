import React from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';

const Navbar = (): JSX.Element => {
  const { isAuthenticated, logout } = useAuth(); // ← Asegúrate de incluir isAuthenticated


  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="bg-blue-700 text-white shadow-md">
      <div className="max-w-7xl mx-auto px-6 py-3">
        {/* Título y botón en columnas separadas */}
        <div className="flex justify-between items-center">
          <div className="flex-shrink-0">
            <h1 className="text-xl font-semibold tracking-wide">
              🎓 Sistema de Análisis de Videos
            </h1>
            {/* Estado de autenticación para depuración */}
            <p className="text-xs italic mt-1">
              Estado actual: {isAuthenticated ? 'Autenticado ✅' : 'No autenticado ❌'}
            </p>
          </div>

          {/* Mostrar botón solo si está autenticado */}
          {isAuthenticated && (
            <div>
              <button
                onClick={handleLogout}
                className="text-xs bg-red-500 hover:bg-red-600 transition px-2 py-1 rounded focus:outline-none focus:ring-1 focus:ring-red-300"
              >
                🔒 Cerrar sesión
              </button>
            </div>
          )}
        </div>

        {/* Menú de navegación centrado */}
        <nav className="mt-3 flex justify-center gap-6 text-sm font-medium">
          <Link to="/dashboard" className="hover:underline hover:text-gray-200">
            📊 Dashboard
          </Link>
          <Link to="/videos" className="hover:underline hover:text-gray-200">
            🎬 Videos
          </Link>
          <Link to="/upload" className="hover:underline hover:text-gray-200">
            📤 Subir Video
          </Link>
        </nav>
      </div>
    </header>
  );
};

export default Navbar;
