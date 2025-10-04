import ffmpeg
from pathlib import Path
from typing import List, Dict, Optional
from django.conf import settings
from django.core.files import File
from apps.videos.models import Video, Segmento, LogProcesamiento
import logging

logger = logging.getLogger(__name__)


class SegmentationError(Exception):
    """Excepción personalizada para errores de segmentación"""
    pass


class VideoSegmentationService:
    """
    Servicio para segmentar videos en clips individuales
    """
    
    def __init__(self, video: Video):
        self.video = video
        self.segments_dir = settings.MEDIA_ROOT / 'segmentos'
        self.segments_dir.mkdir(exist_ok=True)
        self.thumbnails_dir = settings.MEDIA_ROOT / 'miniaturas_segmentos'
        self.thumbnails_dir.mkdir(exist_ok=True)
    
    def segment_video(self, video_path: Path) -> List[Dict]:
        """
        Segmentar video en clips según segmentos identificados por IA
        
        Args:
            video_path: Ruta del video completo
        
        Returns:
            List[Dict]: Lista de segmentos procesados con rutas
        
        Raises:
            SegmentationError: Si hay error en la segmentación
        """
        try:
            self._log_progress('segmentacion', 'iniciado', 'Iniciando segmentación de video')
            
            # Validar archivo
            if not video_path.exists():
                raise SegmentationError(f"Video no existe: {video_path}")
            
            # Obtener segmentos a procesar
            segmentos = self.video.segmentos.all().order_by('orden')
            
            if not segmentos.exists():
                logger.warning(f'No hay segmentos para procesar en video {self.video.id}')
                return []
            
            logger.info(f'Segmentando video {self.video.id} en {segmentos.count()} clips')
            
            resultados = []
            
            for segmento in segmentos:
                try:
                    # Recortar segmento
                    segment_path = self._cut_segment(video_path, segmento)
                    
                    # Generar miniatura del segmento
                    thumbnail_path = self._generate_segment_thumbnail(video_path, segmento)
                    
                    # Actualizar modelo con rutas
                    self._update_segment_files(segmento, segment_path, thumbnail_path)
                    
                    resultados.append({
                        'segmento_id': segmento.id,
                        'titulo': segmento.titulo,
                        'video_path': str(segment_path),
                        'thumbnail_path': str(thumbnail_path),
                        'duracion': segmento.duracion_seg
                    })
                    
                    logger.info(f'Segmento {segmento.id} procesado: {segment_path.name}')
                
                except Exception as e:
                    logger.error(f'Error procesando segmento {segmento.id}: {str(e)}')
                    continue
            
            self._log_progress(
                'segmentacion',
                'completado',
                f'{len(resultados)} segmentos procesados exitosamente'
            )
            
            logger.info(f'Segmentación completada para video {self.video.id}')
            
            return resultados
        
        except Exception as e:
            error_msg = f"Error al segmentar video: {str(e)}"
            self._log_progress('segmentacion', 'error', error_msg, str(e))
            logger.error(error_msg)
            raise SegmentationError(error_msg)
    
    def _cut_segment(self, video_path: Path, segmento: Segmento) -> Path:
        """
        Recortar un segmento específico del video
        
        Args:
            video_path: Ruta del video completo
            segmento: Modelo Segmento con timestamps
        
        Returns:
            Path: Ruta del segmento recortado
        """
        try:
            # Definir nombre de archivo
            output_filename = f'segmento_{self.video.id}_{segmento.orden}.mp4'
            output_path = self.segments_dir / output_filename
            
            # Calcular duración
            inicio = segmento.timestamp_inicio_seg
            duracion = segmento.duracion_seg
            
            logger.info(f'Recortando segmento: {inicio}s por {duracion}s')
            
            # Recortar con FFmpeg
            stream = ffmpeg.input(str(video_path), ss=inicio, t=duracion)
            
            # Configurar output con re-encoding para garantizar compatibilidad
            stream = ffmpeg.output(
                stream,
                str(output_path),
                vcodec='libx264',
                acodec='aac',
                preset='medium',
                crf=23,  # Calidad (18-28, menor = mejor)
                **{
                    'movflags': '+faststart',  # Optimizar para streaming
                    'pix_fmt': 'yuv420p'  # Compatibilidad máxima
                }
            )
            
            # Ejecutar
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            
            # Verificar que se creó
            if not output_path.exists():
                raise SegmentationError(f"No se pudo crear segmento: {output_path}")
            
            logger.info(f'Segmento creado: {output_path}')
            
            return output_path
        
        except ffmpeg.Error as e:
            error_msg = f"Error de FFmpeg: {e.stderr.decode() if e.stderr else str(e)}"
            logger.error(error_msg)
            raise SegmentationError(error_msg)
        
        except Exception as e:
            error_msg = f"Error inesperado al recortar: {str(e)}"
            logger.error(error_msg)
            raise SegmentationError(error_msg)
    
    def _generate_segment_thumbnail(self, video_path: Path, segmento: Segmento) -> Path:
        """
        Generar miniatura para un segmento
        
        Args:
            video_path: Ruta del video completo
            segmento: Modelo Segmento
        
        Returns:
            Path: Ruta de la miniatura
        """
        try:
            # Definir nombre de archivo
            thumbnail_filename = f'thumb_seg_{self.video.id}_{segmento.orden}.jpg'
            thumbnail_path = self.thumbnails_dir / thumbnail_filename
            
            # Capturar frame del medio del segmento
            timestamp = segmento.timestamp_inicio_seg + (segmento.duracion_seg / 2)
            
            # Generar miniatura
            stream = ffmpeg.input(str(video_path), ss=timestamp)
            stream = ffmpeg.output(
                stream,
                str(thumbnail_path),
                vframes=1,
                format='image2',
                vcodec='mjpeg',
                **{'q:v': 2}
            )
            
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            
            if not thumbnail_path.exists():
                logger.warning(f'No se pudo crear miniatura para segmento {segmento.id}')
                return None
            
            logger.info(f'Miniatura creada: {thumbnail_path}')
            
            return thumbnail_path
        
        except Exception as e:
            logger.error(f'Error generando miniatura: {str(e)}')
            return None
    
    def _update_segment_files(self, segmento: Segmento, video_path: Path, thumbnail_path: Optional[Path]):
        """
        Actualizar modelo Segmento con rutas de archivos
        
        Args:
            segmento: Modelo Segmento
            video_path: Ruta del video del segmento
            thumbnail_path: Ruta de la miniatura (opcional)
        """
        try:
            # Guardar video del segmento
            with open(video_path, 'rb') as f:
                segmento.ruta_archivo_segmento.save(
                    video_path.name,
                    File(f),
                    save=False
                )
            
            # Guardar miniatura si existe
            if thumbnail_path and thumbnail_path.exists():
                with open(thumbnail_path, 'rb') as f:
                    segmento.miniatura_url.save(
                        thumbnail_path.name,
                        File(f),
                        save=False
                    )
            
            segmento.save()
            
            logger.info(f'Segmento {segmento.id} actualizado con archivos')
        
        except Exception as e:
            logger.error(f'Error actualizando segmento: {str(e)}')
            raise
    
    def cut_segment_by_time(self, video_path: Path, start: int, end: int, output_name: str = None) -> Path:
        """
        Recortar un segmento específico por timestamps (uso manual)
        
        Args:
            video_path: Ruta del video
            start: Segundo de inicio
            end: Segundo de fin
            output_name: Nombre del archivo de salida (opcional)
        
        Returns:
            Path: Ruta del segmento recortado
        """
        try:
            if not output_name:
                output_name = f'segment_{start}_{end}.mp4'
            
            output_path = self.segments_dir / output_name
            duracion = end - start
            
            stream = ffmpeg.input(str(video_path), ss=start, t=duracion)
            stream = ffmpeg.output(
                stream,
                str(output_path),
                vcodec='libx264',
                acodec='aac',
                preset='medium',
                crf=23
            )
            
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            
            return output_path
        
        except Exception as e:
            logger.error(f'Error recortando segmento manual: {str(e)}')
            raise SegmentationError(f"Error recortando segmento: {str(e)}")
    
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


def segment_video(video_id: int, video_path: Path) -> List[Dict]:
    """
    Función helper para segmentar un video
    
    Args:
        video_id: ID del video
        video_path: Ruta del video completo
    
    Returns:
        List[Dict]: Lista de segmentos procesados
    """
    try:
        video = Video.objects.get(id=video_id)
        service = VideoSegmentationService(video)
        return service.segment_video(video_path)
    except Video.DoesNotExist:
        raise SegmentationError(f"Video con ID {video_id} no existe")