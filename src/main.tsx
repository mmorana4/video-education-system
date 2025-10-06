import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext'; // ← Importa el contexto
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
     <AuthProvider> {/* ← Envuelve tu app */}
      <App />
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
);
