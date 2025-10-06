import React, { createContext, useState, useContext, useEffect } from 'react';

type AuthContextType = {
  isAuthenticated: boolean;
  login: (token: string) => void;
  logout: () => void;
};

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // 🔄 Sincroniza con localStorage al montar
  useEffect(() => {
    const token = localStorage.getItem('access');
    setIsAuthenticated(!!token);
  }, []);

  const login = (token: string) => {
    localStorage.setItem('access', token);
    setIsAuthenticated(true);
  };

  const logout = () => {
    localStorage.removeItem('access');
    localStorage.removeItem('refresh');
    setIsAuthenticated(false);
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth debe usarse dentro de un AuthProvider');
  }
  return context;
}

