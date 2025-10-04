import { useEffect, useState } from "react";

type Video = {
  id: string;
  title: string;
  analyzed: boolean;
  uploadedAt: string;
};

export default function DashboardPage() {
  const [videos, setVideos] = useState<Video[]>([]);

  useEffect(() => {
    const mockVideos: Video[] = [
      {
        id: "1",
        title: "Introducción a la Física",
        analyzed: true,
        uploadedAt: "2025-10-01",
      },
      {
        id: "2",
        title: "Matemáticas para secundaria",
        analyzed: false,
        uploadedAt: "2025-10-02",
      },
    ];
    setVideos(mockVideos);
  }, []);

  const total = videos.length;
  const analyzed = videos.filter((v) => v.analyzed).length;
  const pending = total - analyzed;
  const progress = total > 0 ? Math.round((analyzed / total) * 100) : 0;

  return (
    <div className="max-w-5xl mx-auto mt-10 p-6 space-y-8">
      <h2 className="text-3xl font-bold text-blue-700 text-center">
        📊 Panel de Control Educativo
      </h2>

      {/* Estadísticas */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-center">
        <div className="bg-white border rounded-lg p-4 shadow-sm">
          <p className="text-sm text-gray-500">🎬 Total de videos</p>
          <p className="text-2xl font-bold text-blue-700">{total}</p>
        </div>
        <div className="bg-white border rounded-lg p-4 shadow-sm">
          <p className="text-sm text-gray-500">✅ Analizados</p>
          <p className="text-2xl font-bold text-green-600">{analyzed}</p>
        </div>
        <div className="bg-white border rounded-lg p-4 shadow-sm">
          <p className="text-sm text-gray-500">⏳ Pendientes</p>
          <p className="text-2xl font-bold text-yellow-600">{pending}</p>
        </div>
        <div className="bg-white border rounded-lg p-4 shadow-sm flex flex-col items-center justify-center">
          <p className="text-sm text-gray-500 mb-2">📈 Progreso</p>
          <div className="relative w-20 h-20">
            <svg className="absolute top-0 left-0 w-full h-full">
              <circle
                cx="40"
                cy="40"
                r="30"
                stroke="#e5e7eb"
                strokeWidth="8"
                fill="none"
              />
              <circle
                cx="40"
                cy="40"
                r="30"
                stroke="#3b82f6"
                strokeWidth="8"
                fill="none"
                strokeDasharray="188.4"
                strokeDashoffset={188.4 - (188.4 * progress) / 100}
                strokeLinecap="round"
                transform="rotate(-90 40 40)"
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center text-sm font-semibold text-blue-700">
              {progress}%
            </div>
          </div>
        </div>
      </div>

      {/* Actividad reciente */}
      <div>
        <h3 className="text-xl font-semibold text-gray-800 mb-4">
          🕒 Actividad reciente
        </h3>
        <ul className="space-y-3">
          {videos.map((video) => (
            <li
              key={video.id}
              className="border p-4 rounded-lg bg-white shadow-sm flex justify-between items-center"
            >
              <div>
                <p className="font-medium text-gray-700">{video.title}</p>
                <p className="text-sm text-gray-500">
                  Subido el {video.uploadedAt}
                </p>
              </div>
              <span
                className={`px-3 py-1 rounded-full text-xs font-semibold ${
                  video.analyzed
                    ? "bg-green-100 text-green-700"
                    : "bg-yellow-100 text-yellow-700"
                }`}
              >
                {video.analyzed ? "✅ Analizado" : "⏳ Pendiente"}
              </span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
