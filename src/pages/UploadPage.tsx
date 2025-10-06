import { useState, useEffect } from 'react';
import { FiUploadCloud } from 'react-icons/fi';

const MAX_FILE_SIZE_MB = 100;

const UploadPage = () => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState<'success' | 'error'>('success');
  const [uploading, setUploading] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);

  const handleUpload = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setMessage('');

    if (!title || !description || !videoFile) {
      setMessage('❌ Por favor completa todos los campos');
      setMessageType('error');
      return;
    }

    if (videoFile.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
      setMessage(`❌ El archivo supera los ${MAX_FILE_SIZE_MB} MB`);
      setMessageType('error');
      return;
    }

    const formData = new FormData();
    formData.append('title', title);
    formData.append('description', description);
    formData.append('video', videoFile);

    try {
      setUploading(true);
      const token = localStorage.getItem('access');
      const response = await fetch(`${import.meta.env.VITE_API_URL}/videos/`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      const data = await response.json();
      if (response.ok) {
        setMessage('✅ Video subido exitosamente');
        setMessageType('success');
        setTitle('');
        setDescription('');
        setVideoFile(null);
        setPreviewUrl(null);
        setShowConfirmation(true);
        setTimeout(() => setShowConfirmation(false), 3000);
      } else {
        setMessage(data.detail || '❌ Error al subir el video');
        setMessageType('error');
      }
    } catch {
      setMessage('❌ Error de conexión con el servidor');
      setMessageType('error');
    } finally {
      setUploading(false);
    }
  };

  useEffect(() => {
    if (videoFile) {
      const url = URL.createObjectURL(videoFile);
      setPreviewUrl(url);
      return () => URL.revokeObjectURL(url);
    }
  }, [videoFile]);

  useEffect(() => {
    if (message) {
      const timer = setTimeout(() => setMessage(''), 4000);
      return () => clearTimeout(timer);
    }
  }, [message]);

  return (
    <>
      {/* ✅ Modal de confirmación */}
      {showConfirmation && (
        <div className="fixed inset-0 flex items-center justify-center z-50 bg-black bg-opacity-40">
          <div className="bg-white px-6 py-4 rounded-lg shadow-xl text-center animate-fade-in">
            <h3 className="text-lg font-semibold text-green-600 mb-2">✅ ¡Video guardado!</h3>
            <p className="text-gray-700">Tu video educativo ha sido subido correctamente.</p>
          </div>
        </div>
      )}

      {/* ✅ Toast flotante */}
      {message && (
        <div
          className={`fixed top-4 left-1/2 transform -translate-x-1/2 px-4 py-2 rounded shadow-lg z-50 transition-opacity duration-300 ${
            messageType === 'success' ? 'bg-green-600 text-white' : 'bg-red-600 text-white'
          }`}
        >
          {message}
        </div>
      )}

      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-100 to-purple-200 animate-fade-in">
        <div className="w-full max-w-xl p-8 bg-white border border-gray-300 rounded-xl shadow-xl">
          <div className="flex items-center justify-center mb-6 text-blue-600">
            <FiUploadCloud className="text-3xl mr-2" />
            <h2 className="text-2xl font-bold text-center">Subir Video Educativo</h2>
          </div>

          <form onSubmit={handleUpload} className="space-y-6">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">🎓 Título del video</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition"
                placeholder="Ej. Introducción a la Física"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">📝 Descripción</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-purple-500 transition"
                placeholder="Describe brevemente el contenido del video"
                rows={3}
                required
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">📁 Archivo de video</label>
              <input
                type="file"
                accept="video/*"
                onChange={(e) => setVideoFile(e.target.files?.[0] || null)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 transition"
                required
              />
              {videoFile && (
                <p className="mt-2 text-sm text-gray-600">Archivo seleccionado: {videoFile.name}</p>
              )}
            </div>

            {previewUrl && (
              <div className="mt-4">
                <label className="block text-sm font-semibold text-gray-700 mb-1">🎬 Vista previa</label>
                <video src={previewUrl} controls className="w-full rounded-lg shadow-md" />
              </div>
            )}

            <button
              type="submit"
              disabled={uploading}
              className={`w-full py-2 font-semibold rounded-lg transition duration-300 shadow-md ${
                uploading
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-gradient-to-r from-blue-500 to-purple-600 text-white hover:from-blue-600 hover:to-purple-700'
              }`}
            >
              {uploading ? '📤 Subiendo...' : '🚀 Subir Video'}
            </button>
          </form>
        </div>
      </div>
    </>
  );
};

export default UploadPage;
