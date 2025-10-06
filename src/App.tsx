import { Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import VideosPage from './pages/VideosPage';
import VideoDetailPage from './pages/VideoDetailPage';
import UploadPage from './pages/UploadPage';
import Layout from './components/Layout';
import PrivateRoute from './components/PrivateRoute';

function App() {
  return (
    <Routes>
      {/* Rutas públicas */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* Rutas protegidas con Layout */}
      <Route
        path="/"
        element={
          <PrivateRoute>
            <Layout />
          </PrivateRoute>
        }
      >
        {/* Ruta index para redirigir desde "/" */}
        <Route index element={<Navigate to="/dashboard" replace />} />

        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="videos" element={<VideosPage />} />
        <Route path="videos/:id" element={<VideoDetailPage />} />
        <Route path="upload" element={<UploadPage />} />
      </Route>
    </Routes>
  );
}

export default App;




