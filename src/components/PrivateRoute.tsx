import React, { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

type PrivateRouteProps = {
  children: JSX.Element;
};

const PrivateRoute = ({ children }: PrivateRouteProps): JSX.Element => {
  const { isAuthenticated } = useAuth();
  const [checkingAuth, setCheckingAuth] = useState(true);

  useEffect(() => {
    // Simula carga inicial para evitar redirección antes de sincronizar
    const timer = setTimeout(() => {
      setCheckingAuth(false);
    }, 50); // puedes ajustar el tiempo si lo necesitas

    return () => clearTimeout(timer);
  }, []);

  if (checkingAuth) {
    return <div className="text-center text-white py-10">Verificando acceso...</div>;
  }

  return isAuthenticated ? children : <Navigate to="/login" replace />;
};

export default PrivateRoute;
