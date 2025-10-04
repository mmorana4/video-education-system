import ffmpeg
from pathlib import Path
from django.conf import settings
from apps.videos.models import Video, LogProcesamiento
import logging

logger = logging.getLogger(__name__)


class AudioExtractionError(Exception):
    """Excepción personalizada para errores de extracción de audio"""
    pass


class AudioExtractor:
    """
    Servicio para extraer audio de videos usando FFmpeg
    """
    
    def __init__(self, video: Video):
        self.video = video
        self.audio_dir = settings.MEDIA_ROOT / 'audio'
        self.audio_dir.mkdir(exist_ok=True)
    
    def extract(self, video_path: Path) -> Path:
        """
        Extraer audio del video
        
        Args:
            video_path: Ruta del archivo de video
        
        Returns:
            Path: Ruta del archivo de audio extraído
        
        Raises:
            AudioExtractionError: Si hay error en la extracción
        """
        try:
            self._log_progress('extraccion_audio', 'iniciado', 'Iniciando extracción de audio')
            
            # Validar que el archivo existe
            if not video_path.exists():
                raise AudioExtractionError(f"Archivo de video no existe: {video_path}")
            
            # Definir ruta de salida
            output_path = self.audio_dir / f'audio_{self.video.id}.mp3'
            
            # Extraer audio con FFmpeg
            stream = ffmpeg.input(str(video_path))
            stream = ffmpeg.output(
                stream,
                str(output_path),
                acodec='libmp3lame',
                audio_bitrate='128k',
                ar='16000',  # Sample rate 16kHz (óptimo para speech recognition)
                ac=1  # Mono
            )
            
            # Ejecutar con sobrescritura
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            
            # Verificar que se creó el archivo
            if not output_path.exists():
                raise AudioExtractionError("No se pudo crear el archivo de audio")
            
            # Obtener información del audio
            audio_info = self._get_audio_info(output_path)
            
            self._log_progress(
                'extraccion_audio',
                'completado',
                f'Audio extraído: {output_path}',
            )
            
            return output_path
        
        except ffmpeg.Error as e:
            error_msg = f"Error de FFmpeg al extraer audio: {e.stderr.decode() if e.stderr else str(e)}"
            self._log_progress('extraccion_audio', 'error', error_msg, str(e))
            raise AudioExtractionError(error_msg)
        
        except Exception as e:
            error_msg = f"Error inesperado al extraer audio: {str(e)}"
            self._log_progress('extraccion_audio', 'error', error_msg, str(e))
            raise AudioExtractionError(error_msg)
    
    def _get_audio_info(self, audio_path: Path) -> dict:
        """
        Obtener información del archivo de audio
        
        Args:
            audio_path: Ruta del archivo de audio
        
        Returns:
            dict: Información del audio
        """
        try:
            probe = ffmpeg.probe(str(audio_path))
            audio_stream = next(
                (stream for stream in probe['streams'] if stream['codec_type'] == 'audio'),
                None
            )
            
            if audio_stream:
                return {
                    'codec': audio_stream.get('codec_name', ''),
                    'bitrate': audio_stream.get('bit_rate', ''),
                    'sample_rate': audio_stream.get('sample_rate', ''),
                    'channels': audio_stream.get('channels', 0),
                    'duration': float(audio_stream.get('duration', 0)),
                }
            
            return {}
        
        except Exception as e:
            logger.error(f"Error al obtener info del audio: {str(e)}")
            return {}
    
    def _log_progress(self, etapa: str, estado: str, mensaje: str, error_detalle: str = None):
        """Registrar progreso en la base de datos"""
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


def extract_audio(video_id: int, video_path: Path) -> Path:
    """
    Función helper para extraer audio de un video
    
    Args:
        video_id: ID del video
        video_path: Ruta del archivo de video
    
    Returns:
        Path: Ruta del archivo de audio
    """
    try:
        video = Video.objects.get(id=video_id)
        extractor = AudioExtractor(video)
        return extractor.extract(video_path)
    except Video.DoesNotExist:
        raise AudioExtractionError(f"Video con ID {video_id} no existe")