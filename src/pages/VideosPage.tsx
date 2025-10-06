import { useEffect, useState } from "react";
import React from "react";
import { useNavigate } from "react-router-dom";

type Video = {
  id: number;
  titulo: string;
  fuente: string;
  duracion_formateada?: string;
  miniatura_url?: string;
  ruta_video_completo?: string;
};

export default function VideosPage() {
  const [videos, setVideos] = useState<Video[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [videoAEliminar, setVideoAEliminar] = useState<Video | null>(null);
  const [mensaje, setMensaje] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchVideos = async () => {
      const token = localStorage.getItem("access");

      if (!token) {
        navigate("/login");
        return;
      }

      try {
        const response = await fetch(`${import.meta.env.VITE_API_URL}/videos/`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (response.ok) {
          const data = await response.json();
          setVideos(Array.isArray(data.results) ? data.results : []);
        } else if (response.status === 401) {
          navigate("/login");
        } else {
          setError("No se pudieron cargar los videos.");
        }
      } catch {
        setError("Error de conexión con el servidor.");
      }
    };

    fetchVideos();
  }, [navigate]);

  useEffect(() => {
    if (mensaje) {
      const timer = setTimeout(() => setMensaje(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [mensaje]);

  const confirmarEliminacion = async () => {
    if (!videoAEliminar) return;

    const token = localStorage.getItem("access");

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/videos/${videoAEliminar.id}/`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok || response.status === 204) {
        setVideos((prev) => prev?.filter((v) => v.id !== videoAEliminar.id) || []);
        setMensaje(`✅ Video "${videoAEliminar.titulo}" eliminado correctamente.`);
        setVideoAEliminar(null);
      } else {
        setMensaje("❌ No se pudo eliminar el video.");
      }
    } catch {
      setMensaje("❌ Error de conexión al eliminar.");
    }
  };

  const handleView = (id: number) => {
    navigate(`/videos/${id}`);
  };

  return (
    <>
      {/* Toast flotante */}
      {mensaje && (
        <div className="fixed top-4 left-1/2 transform -translate-x-1/2 bg-green-600 text-white px-4 py-2 rounded shadow-lg z-50 transition-opacity duration-300">
          {mensaje}
        </div>
      )}

      <div className="max-w-4xl mx-auto mt-10 p-6 space-y-6">
        <h2 className="text-2xl font-bold text-blue-700 text-center">
          🎬 Videos Educativos Subidos
        </h2>

        {error ? (
          <p className="text-red-500 text-center">{error}</p>
        ) : videos === null ? (
          <p className="text-gray-500 text-center">Cargando videos...</p>
        ) : videos.length === 0 ? (
          <p className="text-gray-500 text-center">No hay videos disponibles.</p>
        ) : (
          videos.map((video) => (
            <div key={video.id} className="border rounded-lg p-4 shadow-sm space-y-2 bg-white">
              <h3 className="text-lg font-semibold text-gray-800">{video.titulo}</h3>
              <p className="text-sm text-gray-600">Fuente: {video.fuente}</p>
              <p className="text-sm text-gray-600">
                Duración: {video.duracion_formateada && video.duracion_formateada !== "00:00:00"
                  ? video.duracion_formateada
                  : "No disponible"}
              </p>

              {video.miniatura_url && (
                <img
                  src={`${import.meta.env.VITE_API_URL}${video.miniatura_url}`}
                  alt="Miniatura del video"
                  className="w-full rounded-md"
                />
              )}

              {video.ruta_video_completo && (
                <video
                  src={video.ruta_video_completo}
                  controls
                  className="w-full max-w-sm mx-auto rounded-md"
                />
              )}

              <div className="flex gap-4 mt-2">
                <button
                  onClick={() => setVideoAEliminar(video)}
                  className="bg-red-500 text-white px-4 py-1 rounded hover:bg-red-600 transition"
                >
                  Eliminar
                </button>

                <button
                  onClick={() => handleView(video.id)}
                  className="bg-blue-500 text-white px-4 py-1 rounded hover:bg-blue-600 transition"
                >
                  Ver Detalles
                </button>
              </div>
            </div>
          ))
        )}

        {/* Modal de confirmación */}
        {videoAEliminar && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white p-6 rounded-lg shadow-lg max-w-sm w-full space-y-4">
              <h3 className="text-lg font-semibold text-gray-800 text-center">
                ¿Eliminar video?
              </h3>
              <p className="text-sm text-gray-600 text-center">
                Estás a punto de eliminar <strong>{videoAEliminar.titulo}</strong>. Esta acción no se puede deshacer.
              </p>
              <div className="flex justify-center gap-4 mt-4">
                <button
                  onClick={() => setVideoAEliminar(null)}
                  className="px-4 py-2 bg-gray-300 rounded hover:bg-gray-400"
                >
                  Cancelar
                </button>
                <button
                  onClick={confirmarEliminacion}
                  className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
                >
                  Eliminar
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
