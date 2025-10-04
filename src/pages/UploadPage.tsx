import React, { useState } from 'react';

const UploadPage = (): JSX.Element => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [progress, setProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!title || !description || !file) {
      alert('Por favor completa todos los campos.');
      return;
    }

    setIsUploading(true);
    setProgress(0);

    const fakeUpload = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(fakeUpload);
          setIsUploading(false);
          alert('Video subido exitosamente 🎉');
          setTitle('');
          setDescription('');
          setFile(null);
          return 100;
        }
        return prev + 10;
      });
    }, 300);
  };

  return (
    <div className="max-w-3xl mx-auto bg-white p-8 rounded-lg shadow-md">
      <h2 className="text-3xl font-bold mb-6 text-center text-blue-700">
        🎓 Subir Video Educativo
      </h2>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Título */}
        <div className="flex flex-col">
          <label className="text-sm font-semibold text-gray-700 mb-2">Título</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="border border-gray-300 rounded-md px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400"
            placeholder="Ej. Introducción a la Física"
          />
        </div>

        {/* Descripción */}
        <div className="flex flex-col">
          <label className="text-sm font-semibold text-gray-700 mb-2">Descripción</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="border border-gray-300 rounded-md px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400"
            rows={5}
            placeholder="Describe brevemente el contenido del video"
          />
        </div>

        {/* Archivo */}
        <div className="flex flex-col">
          <label className="text-sm font-semibold text-gray-700 mb-2">Archivo de video</label>
          <input
            type="file"
            accept="video/*"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="border border-gray-300 rounded-md px-4 py-2 bg-white file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-blue-600 file:text-white hover:file:bg-blue-700"
          />
        </div>

        {/* Barra de progreso */}
        {isUploading && (
          <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
            <div
              className="bg-blue-600 h-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        )}

        {/* Botón */}
        <button
          type="submit"
          disabled={isUploading}
          className={`w-full bg-blue-600 text-white font-semibold py-3 rounded-md hover:bg-blue-700 transition ${
            isUploading ? 'opacity-50 cursor-not-allowed' : ''
          }`}
        >
          {isUploading ? 'Subiendo...' : 'Subir Video'}
        </button>
      </form>
    </div>
  );
};

export default UploadPage;

