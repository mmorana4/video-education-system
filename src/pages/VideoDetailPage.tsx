import { useParams } from "react-router-dom";
import { useEffect, useRef, useState } from "react";

type Video = {
  id: number;
  titulo: string;
  fuente: string;
  estado: string;
  duracion_formateada?: string;
  ruta_video_completo?: string;
};

export default function VideoDetailPage() {
  const { id } = useParams();
  const [video, setVideo] = useState<Video | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [promptResult, setPromptResult] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    const token = localStorage.getItem("access");

    const fetchVideo = async () => {
      try {
        const response = await fetch(`${import.meta.env.VITE_API_URL}/videos/${id}/`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (response.ok) {
          const data = await response.json();
          setVideo(data);
        } else {
          setError("No se pudo cargar el video.");
        }
      } catch (err) {
        setError("Error de conexión.");
      }
    };

    fetchVideo();
  }, [id]);

  const formatDuration = (duration: string): string => {
    return duration && duration !== "00:00:00" ? duration : "No disponible";
  };

  const handleAnalyze = () => {
    setIsAnalyzing(true);
    setProgress(0);
    setPromptResult(null);

    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          return 100;
        }
        return prev + 5;
      });
    }, 120);

    setTimeout(() => {
      const result = `
🧠 *Análisis educativo del video "${video?.titulo}"*

📄 *Transcripción simulada:*
"Bienvenidos a esta clase de informática. Hoy exploraremos los componentes básicos del hardware, el rol del software y cómo funcionan las redes..."

🔑 *Palabras clave detectadas:*
informática, hardware, software, redes, tecnología, fundamentos

📊 *Métricas educativas:*
- Claridad del contenido: 92%
- Conceptos identificados: 7
- Nivel estimado: Básico - Intermedio

✅ Este análisis puede servir como base para retroalimentación, resumen del contenido o generación de preguntas educativas.
      `;
      setPromptResult(result.trim());
      setIsAnalyzing(false);
    }, 2500);
  };

  if (error) {
    return <p className="text-center mt-10 text-red-500">{error}</p>;
  }

  if (!video) {
    return <p className="text-center mt-10 text-gray-500">Cargando video...</p>;
  }

  return (
    <div className="max-w-3xl mx-auto mt-10 p-6 bg-white rounded-lg shadow space-y-6">
      <h2 className="text-2xl font-bold text-blue-700 text-center">{video.titulo}</h2>
      <p className="text-gray-600 text-center">Fuente: {video.fuente}</p>
      <p className="text-gray-600 text-center">Estado: {video.estado}</p>
      <p className="text-sm text-gray-500 text-center">
        Duración del video: {formatDuration(video.duracion_formateada || "")}
      </p>

      {video.ruta_video_completo && (
        <div className="flex flex-col items-center space-y-4">
          <div className="w-full flex justify-center">
            <video
              ref={videoRef}
              src={video.ruta_video_completo}
              controls
              className="w-full max-w-[360px] aspect-video rounded-md"
            />
          </div>

          <div className="w-full flex justify-center">
            <button
              onClick={handleAnalyze}
              disabled={isAnalyzing}
              className={`px-4 py-2 rounded transition ${
                isAnalyzing
                  ? "bg-gray-400 cursor-not-allowed"
                  : "bg-green-600 text-white hover:bg-green-700"
              }`}
            >
              {isAnalyzing ? "Analizando..." : "Iniciar análisis"}
            </button>
          </div>
        </div>
      )}

      {isAnalyzing && (
        <div className="mt-4 space-y-2">
          <p className="text-blue-600 font-medium text-center">
            🔄 Analizando video educativo...
          </p>
          <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
            <div
              className="bg-blue-500 h-3 transition-all duration-100 ease-linear"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
        </div>
      )}

      {promptResult && (
        <div className="mt-6 space-y-4 border-t pt-4 bg-gray-50 p-4 rounded">
          <h3 className="text-xl font-semibold text-gray-800 text-center">
            🧠 Resultado del análisis
          </h3>
          <pre className="whitespace-pre-wrap text-sm text-gray-700">{promptResult}</pre>
        </div>
      )}
    </div>
  );
}
