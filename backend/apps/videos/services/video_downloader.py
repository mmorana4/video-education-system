import os
import yt_dlp
from pathlib import Path
from django.conf import settings
from apps.videos.models import Video, LogProcesamiento
import logging

logger = logging.getLogger(__name__)


class VideoDownloadError(Exception):
    """Excepción personalizada para errores de descarga"""
    pass


class VideoDownloader:
    """
    Servicio para descargar videos de diferentes plataformas
    """
    
    def __init__(self, video: Video):
        self.video = video
        self.temp_dir = settings.TEMP_ROOT
        self.temp_dir.mkdir(exist_ok=True)
    
    def download(self) -> Path:
        """
        Descargar video desde la URL
        
        Returns:
            Path: Ruta del archivo descargado
        
        Raises:
            VideoDownloadError: Si hay error en la descarga
        """
        try:
            self._log_progress('descarga', 'iniciado', 'Iniciando descarga de video')
            
            # Validar URL
            if not self.video.url_original:
                raise VideoDownloadError("No se proporcionó URL de video")
            
            # Configurar yt-dlp
            output_template = str(self.temp_dir / f'video_{self.video.id}_%(id)s.%(ext)s')
            
            ydl_opts = {
                'format': settings.YT_DLP_FORMAT,
                'outtmpl': output_template,
                'ratelimit': self._parse_rate_limit(settings.YT_DLP_RATE_LIMIT),
                'progress_hooks': [self._progress_hook],
                'quiet': False,
                'no_warnings': False,
            }
            
            # Descargar video
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.video.url_original, download=True)
                
                # Obtener ruta del archivo descargado
                downloaded_file = Path(ydl.prepare_filename(info))
                
                # Actualizar información del video
                self._update_video_info(info, downloaded_file)
                
                self._log_progress('descarga', 'completado', f'Video descargado: {downloaded_file}')
                
                return downloaded_file
        
        except yt_dlp.utils.DownloadError as e:
            error_msg = f"Error al descargar video: {str(e)}"
            self._log_progress('descarga', 'error', error_msg, str(e))
            raise VideoDownloadError(error_msg)
        
        except Exception as e:
            error_msg = f"Error inesperado en descarga: {str(e)}"
            self._log_progress('descarga', 'error', error_msg, str(e))
            raise VideoDownloadError(error_msg)
    
    def get_video_info(self, url: str) -> dict:
        """
        Obtener información del video sin descargarlo
        
        Args:
            url: URL del video
        
        Returns:
            dict: Información del video
        """
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                return {
                    'titulo': info.get('title', 'Sin título'),
                    'duracion': info.get('duration', 0),
                    'formato': info.get('ext', 'mp4'),
                    'resolucion': f"{info.get('width', 0)}x{info.get('height', 0)}",
                    'thumbnail': info.get('thumbnail', ''),
                    'descripcion': info.get('description', ''),
                    'uploader': info.get('uploader', ''),
                }
        
        except Exception as e:
            logger.error(f"Error al obtener info del video: {str(e)}")
            return {}
    
    def validate_url(self, url: str) -> tuple[bool, str]:
        """
        Validar que la URL sea válida y accesible
        
        Args:
            url: URL a validar
        
        Returns:
            tuple: (es_valida, mensaje)
        """
        try:
            info = self.get_video_info(url)
            
            if not info:
                return False, "No se pudo obtener información del video"
            
            # Validar duración
            duracion = info.get('duracion', 0)
            if duracion > settings.MAX_VIDEO_DURATION_SECONDS:
                max_horas = settings.MAX_VIDEO_DURATION_SECONDS / 3600
                return False, f"El video excede la duración máxima de {max_horas} horas"
            
            return True, "URL válida"
        
        except Exception as e:
            return False, f"URL inválida: {str(e)}"
    
    def _update_video_info(self, info: dict, file_path: Path):
        """Actualizar información del video en la base de datos"""
        try:
            # Obtener tamaño del archivo
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            
            # Actualizar modelo
            self.video.titulo = info.get('title', self.video.titulo)
            self.video.duracion_segundos = info.get('duration', 0)
            self.video.formato = info.get('ext', 'mp4')
            self.video.tamano_mb = round(file_size_mb, 2)
            self.video.metadata_json = {
                'resolucion': f"{info.get('width', 0)}x{info.get('height', 0)}",
                'fps': info.get('fps', 0),
                'codec': info.get('vcodec', ''),
                'uploader': info.get('uploader', ''),
                'descripcion': info.get('description', '')[:500],  # Limitar a 500 caracteres
            }
            self.video.estado = 'descargando'
            self.video.save()
        
        except Exception as e:
            logger.error(f"Error al actualizar info del video: {str(e)}")
    
    def _progress_hook(self, d: dict):
        """Hook para trackear progreso de descarga"""
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', '0%')
            speed = d.get('_speed_str', 'N/A')
            logger.info(f"Descargando video {self.video.id}: {percent} - {speed}")
        
        elif d['status'] == 'finished':
            logger.info(f"Descarga completada para video {self.video.id}")
    
    def _parse_rate_limit(self, rate_str: str) -> int:
        """
        Parsear string de rate limit a bytes/segundo
        Ej: '1M' -> 1048576, '500K' -> 512000
        """
        rate_str = rate_str.upper().strip()
        
        if rate_str.endswith('M'):
            return int(float(rate_str[:-1]) * 1024 * 1024)
        elif rate_str.endswith('K'):
            return int(float(rate_str[:-1]) * 1024)
        else:
            return int(rate_str)
    
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


def download_video(video_id: int) -> Path:
    """
    Función helper para descargar un video
    
    Args:
        video_id: ID del video a descargar
    
    Returns:
        Path: Ruta del archivo descargado
    """
    try:
        video = Video.objects.get(id=video_id)
        downloader = VideoDownloader(video)
        return downloader.download()
    except Video.DoesNotExist:
        raise VideoDownloadError(f"Video con ID {video_id} no existe")