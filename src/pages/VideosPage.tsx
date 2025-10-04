import { useEffect, useState } from "react";
import React from "react";
import { useNavigate } from "react-router-dom";

type Video = {
  id: string;
  title: string;
  description: string;
  url: string;
};

export default function VideosPage() {
  const [videos, setVideos] = useState<Video[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    // Simulación de datos (puedes reemplazar con fetch a tu backend)
    const mockVideos: Video[] = [
      {
        id: "1",
        title: "Introducción a la Física",
        description: "Conceptos básicos de movimiento y energía.",
        url: "https://www.w3schools.com/html/mov_bbb.mp4",
      },
      {
        id: "2",
        title: "Matemáticas para secundaria",
        description: "Álgebra y funciones lineales.",
        url: "https://www.w3schools.com/html/movie.mp4",
      },
    ];
    setVideos(mockVideos);
  }, []);

  const handleDelete = (id: string) => {
    if (!confirm("¿Estás seguro de que deseas eliminar este video?")) return;

    // Simulación de eliminación (reemplazar con fetch DELETE)
    setVideos((prev) => prev.filter((v) => v.id !== id));
    alert("Video eliminado (simulado)");
  };

  const handleEdit = (id: string) => {
    alert(`Función de edición para el video ${id} (por implementar)`);
  };

  const handleView = (id: string) => {
    navigate(`/videos/${id}`);
  };

  return (
    <div className="max-w-4xl mx-auto mt-10 p-6 space-y-6">
      <h2 className="text-2xl font-bold text-blue-700 text-center">
        🎬 Videos Educativos Subidos
      </h2>

      {videos.length === 0 ? (
        <p className="text-gray-500 text-center">No hay videos disponibles.</p>
      ) : (
        videos.map((video) => (
          <div
            key={video.id}
            className="border rounded-lg p-4 shadow-sm space-y-2 bg-white"
          >
            <h3 className="text-lg font-semibold text-gray-800">
              {video.title}
            </h3>
            <p className="text-sm text-gray-600">{video.description}</p>
            <video
              src={video.url}
              controls
              className="w-full rounded-md"
            />

            <div className="flex gap-4 mt-2">
              <button
                onClick={() => handleDelete(video.id)}
                className="bg-red-500 text-white px-4 py-1 rounded hover:bg-red-600 transition"
              >
                Eliminar
              </button>

              <button
                onClick={() => handleEdit(video.id)}
                className="bg-yellow-400 text-black px-4 py-1 rounded hover:bg-yellow-500 transition"
              >
                Editar
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
    </div>
  );
}
