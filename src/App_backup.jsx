import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'

import { Routes, Route } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import VideosPage from './pages/VideosPage';
import VideoDetailPage from './pages/VideoDetailPage';
import UploadPage from './pages/UploadPage';
import Layout from './components/Layout';



function App() {
  const [count, setCount] = useState(0)

  return (
    <Routes>
    <Route path="/login" element={<LoginPage />} />
    <Route path="/register" element={<RegisterPage />} />
    <Route path="/dashboard" element={<DashboardPage />} />
    <Route path="/videos" element={<VideosPage />} />
    <Route path="/videos/:id" element={<VideoDetailPage />} />
    <Route path="/upload" element={<UploadPage />} />
  </Routes>
  )
}

export default App
