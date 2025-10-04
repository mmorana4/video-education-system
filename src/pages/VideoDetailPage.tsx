import { useParams } from "react-router-dom";
import { useEffect, useRef, useState } from "react";

type Video = {
  id: string;
  title: string;
  description: string;
  url: string;
  uploadedAt?: string;
};

export default function VideoDetailPage() {
  const { id } = useParams();
  const [video, setVideo] = useState<Video | null>(null);
  const [analysis, setAnalysis] = useState<{
    transcript: string;
    keywords: string[];
    metrics: { clarity: number; concepts: number };
  } | null>(null);
  const [duration, setDuration] = useState<number | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [progress, setProgress] = useState(0);
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    const mockVideos: Video[] = [
      {
        id: "1",
        title: "Introducción a la Física",
        description: "Conceptos básicos de movimiento y energía.",
        url: "https://www.w3schools.com/html/mov_bbb.mp4",
        uploadedAt: "2025-10-01",
      },
      {
        id: "2",
        title: "Matemáticas para secundaria",
        description: "Álgebra y funciones lineales.",
        url: "https://www.w3schools.com/html/movie.mp4",
        uploadedAt: "2025-10-02",
      },
    ];

    const found = mockVideos.find((v) => v.id === id);
    setVideo(found || null);
  }, [id]);

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration);
    }
  };

  const handleAnalyze = () => {
    setIsAnalyzing(true);
    setProgress(0);

    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          return 100;
        }
        return prev + 5;
      });
    }, 120); // 5% cada 120ms → ~2.4s total

    setTimeout(() => {
      setAnalysis({
        transcript:
          "Bienvenidos al curso de física. Hoy hablaremos sobre el movimiento, la energía y cómo se relacionan...",
        keywords: ["movimiento", "energía", "física", "conceptos", "introducción"],
        metrics: {
          clarity: 87,
          concepts: 5,
        },
      });
      setIsAnalyzing(false);
    }, 2500);
  };

  if (!video) {
    return (
      <div className="text-center mt-10 text-gray-500">
        Video no encontrado.
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto mt-10 p-6 bg-white rounded-lg shadow space-y-6">
      <h2 className="text-2xl font-bold text-blue-700">{video.title}</h2>
      <p className="text-gray-600">{video.description}</p>
      <p className="text-sm text-gray-400">
        Fecha de subida: {video.uploadedAt}
      </p>

      <video
        ref={videoRef}
        src={video.url}
        controls
        className="w-full rounded-md"
        onLoadedMetadata={handleLoadedMetadata}
      />

      {duration && (
        <p className="text-sm text-gray-500">
          Duración del video: {Math.floor(duration)} segundos
        </p>
      )}

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

      {analysis && !isAnalyzing && (
        <div className="mt-6 space-y-4 border-t pt-4">
          <h3 className="text-xl font-semibold text-gray-800">
            🧠 Resultados del análisis
          </h3>

          <div>
            <p className="font-medium text-gray-700">Transcripción:</p>
            <p className="text-sm text-gray-600">{analysis.transcript}</p>
          </div>

          <div>
            <p className="font-medium text-gray-700">Palabras clave:</p>
            <ul className="list-disc list-inside text-sm text-gray-600">
              {analysis.keywords.map((word, index) => (
                <li key={index}>{word}</li>
              ))}
            </ul>
          </div>

          <div>
            <p className="font-medium text-gray-700">Métricas educativas:</p>
            <ul className="text-sm text-gray-600">
              <li>Claridad: {analysis.metrics.clarity}%</li>
              <li>Conceptos identificados: {analysis.metrics.concepts}</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
