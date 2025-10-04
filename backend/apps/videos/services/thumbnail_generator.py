import ffmpeg
from pathlib import Path
from django.conf import settings
from django.core.files import File
from apps.videos.models import Video, LogProcesamiento
import logging

logger = logging.getLogger(__name__)


class ThumbnailGenerationError(Exception):
    """Excepción para errores de generación de miniaturas"""
    pass


class ThumbnailGenerator:
    """
    Servicio para generar miniaturas de videos
    """
    
    def __init__(self, video: Video):
        self.video = video
        self.thumbnail_dir = settings.MEDIA_ROOT / 'miniaturas'
        self.thumbnail_dir.mkdir(exist_ok=True)
    
    def generate(self, video_path: Path, timestamp: int = None) -> Path:
        """
        Generar miniatura del video
        
        Args:
            video_path: Ruta del archivo de video
            timestamp: Segundo del video para capturar (None = primer frame)
        
        Returns:
            Path: Ruta de la miniatura generada
        
        Raises:
            ThumbnailGenerationError: Si hay error en la generación
        """
        try:
            self._log_progress('generacion_miniatura', 'iniciado', 'Generando miniatura')
            
            # Validar archivo
            if not video_path.exists():
                raise ThumbnailGenerationError(f"Video no existe: {video_path}")
            
            # Definir timestamp (por defecto 10% de la duración del video)
            if timestamp is None and self.video.duracion_segundos:
                timestamp = int(self.video.duracion_segundos * 0.1)
            elif timestamp is None:
                timestamp = 0
            
            # Definir ruta de salida
            output_path = self.thumbnail_dir / f'thumb_{self.video.id}.jpg'
            
            # Generar miniatura
            stream = ffmpeg.input(str(video_path), ss=timestamp)
            stream = ffmpeg.output(
                stream,
                str(output_path),
                vframes=1,
                format='image2',
                vcodec='mjpeg',
                **{'q:v': 2}  # Calidad (1-31, menor es mejor)
            )
            
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            
            # Verificar que se creó la miniatura
            if not output_path.exists():
                raise ThumbnailGenerationError("No se pudo crear la miniatura")
            
            # Actualizar modelo Video con la ruta de la miniatura
            with open(output_path, 'rb') as f:
                self.video.miniatura_url.save(
                    output_path.name,
                    File(f),
                    save=True
                )
            
            self._log_progress(
                'generacion_miniatura',
                'completado',
                f'Miniatura generada: {output_path}'
            )
            
            return output_path
        
        except ffmpeg.Error as e:
            error_msg = f"Error de FFmpeg: {e.stderr.decode() if e.stderr else str(e)}"
            self._log_progress('generacion_miniatura', 'error', error_msg, str(e))
            raise ThumbnailGenerationError(error_msg)
        
        except Exception as e:
            error_msg = f"Error inesperado: {str(e)}"
            self._log_progress('generacion_miniatura', 'error', error_msg, str(e))
            raise ThumbnailGenerationError(error_msg)
    
    def generate_multiple(self, video_path: Path, count: int = 5) -> list[Path]:
        """
        Generar múltiples miniaturas a intervalos regulares
        
        Args:
            video_path: Ruta del video
            count: Cantidad de miniaturas a generar
        
        Returns:
            list[Path]: Lista de rutas de miniaturas
        """
        thumbnails = []
        
        if not self.video.duracion_segundos:
            return thumbnails
        
        # Calcular intervalos
        interval = self.video.duracion_segundos // (count + 1)
        
        for i in range(1, count + 1):
            timestamp = interval * i
            try:
                output_path = self.thumbnail_dir / f'thumb_{self.video.id}_{i}.jpg'
                
                stream = ffmpeg.input(str(video_path), ss=timestamp)
                stream = ffmpeg.output(
                    stream,
                    str(output_path),
                    vframes=1,
                    format='image2',
                    vcodec='mjpeg',
                    **{'q:v': 2}
                )
                
                ffmpeg.run(stream, overwrite_output=True, quiet=True)
                thumbnails.append(output_path)
            
            except Exception as e:
                logger.error(f"Error generando miniatura {i}: {str(e)}")
        
        return thumbnails
    
    def _log_progress(self, etapa: str, estado: str, mensaje: str, error_detalle: str = None):
        """Registrar progreso"""
        try:
            LogProcesamiento.objects.create(
                video=self.video,
                etapa=etapa,
                estado=estado,
                mensaje=mensaje,
                error_detalle=error_detalle
            )
        except Exception as e:
            logger.error(f"Error al crear log: {str(e)}")


def generate_thumbnail(video_id: int, video_path: Path, timestamp: int = None) -> Path:
    """
    Función helper para generar miniatura
    
    Args:
        video_id: ID del video
        video_path: Ruta del video
        timestamp: Segundo del video para capturar
    
    Returns:
        Path: Ruta de la miniatura
    """
    try:
        video = Video.objects.get(id=video_id)
        generator = ThumbnailGenerator(video)
        return generator.generate(video_path, timestamp)
    except Video.DoesNotExist:
        raise ThumbnailGenerationError(f"Video con ID {video_id} no existe")