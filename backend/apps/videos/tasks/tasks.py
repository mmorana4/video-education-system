from celery import shared_task, chain, group
from celery.utils.log import get_task_logger
from django.utils import timezone
from pathlib import Path
from apps.videos.services.transcription_service import (
    TranscriptionService,
    TranscriptionError
)
from apps.videos.models import Video, LogProcesamiento, Segmento
from apps.videos.services import (
    VideoDownloader,
    AudioExtractor,
    ThumbnailGenerator,
    FileCleaner,
    VideoDownloadError,
    AudioExtractionError,
    ThumbnailGenerationError,
)
from apps.videos.services.analysis_service import (
    AnalysisService,
    AnalysisError
)
from apps.videos.services.video_segmentation_service import (
    VideoSegmentationService,
    SegmentationError
)

logger = get_task_logger(__name__)


@shared_task(bind=True, max_retries=3)
def descargar_video_task(self, video_id: int):
    """
    Tarea asíncrona para descargar un video
    
    Args:
        video_id: ID del video a descargar
    
    Returns:
        str: Ruta del archivo descargado
    """
    try:
        logger.info(f'Iniciando descarga de video {video_id}')
        
        # Obtener video
        video = Video.objects.get(id=video_id)
        
        # Actualizar estado
        video.estado = 'descargando'
        video.save()
        
        # Descargar video
        downloader = VideoDownloader(video)
        video_path = downloader.download()
        
        logger.info(f'Video {video_id} descargado: {video_path}')
        
        return str(video_path)
    
    except Video.DoesNotExist:
        logger.error(f'Video {video_id} no existe')
        raise
    
    except VideoDownloadError as e:
        logger.error(f'Error al descargar video {video_id}: {str(e)}')
        
        # Actualizar estado del video
        try:
            video = Video.objects.get(id=video_id)
            video.estado = 'error'
            video.save()
        except:
            pass
        
        # Reintentar si no se han agotado los intentos
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
    
    except Exception as e:
        logger.error(f'Error inesperado al descargar video {video_id}: {str(e)}')
        
        try:
            video = Video.objects.get(id=video_id)
            video.estado = 'error'
            video.save()
        except:
            pass
        
        raise


@shared_task(bind=True, max_retries=3)
def extraer_audio_task(self, video_id: int, video_path: str):
    """
    Tarea asíncrona para extraer audio de un video
    
    Args:
        video_id: ID del video
        video_path: Ruta del archivo de video
    
    Returns:
        str: Ruta del archivo de audio
    """
    try:
        logger.info(f'Iniciando extracción de audio del video {video_id}')
        
        # Obtener video
        video = Video.objects.get(id=video_id)
        
        # Actualizar estado
        video.estado = 'procesando'
        video.save()
        
        # Extraer audio
        extractor = AudioExtractor(video)
        audio_path = extractor.extract(Path(video_path))
        
        logger.info(f'Audio extraído del video {video_id}: {audio_path}')
        
        return str(audio_path)
    
    except Video.DoesNotExist:
        logger.error(f'Video {video_id} no existe')
        raise
    
    except AudioExtractionError as e:
        logger.error(f'Error al extraer audio del video {video_id}: {str(e)}')
        
        try:
            video = Video.objects.get(id=video_id)
            video.estado = 'error'
            video.save()
        except:
            pass
        
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
    
    except Exception as e:
        logger.error(f'Error inesperado al extraer audio del video {video_id}: {str(e)}')
        
        try:
            video = Video.objects.get(id=video_id)
            video.estado = 'error'
            video.save()
        except:
            pass
        
        raise


@shared_task(bind=True, max_retries=3)
def generar_miniatura_task(self, video_id: int, video_path: str):
    """
    Tarea asíncrona para generar miniatura de un video
    
    Args:
        video_id: ID del video
        video_path: Ruta del archivo de video
    
    Returns:
        str: Ruta de la miniatura generada
    """
    try:
        logger.info(f'Generando miniatura para video {video_id}')
        
        # Obtener video
        video = Video.objects.get(id=video_id)
        
        # Generar miniatura
        generator = ThumbnailGenerator(video)
        thumbnail_path = generator.generate(Path(video_path))
        
        logger.info(f'Miniatura generada para video {video_id}: {thumbnail_path}')
        
        return str(thumbnail_path)
    
    except Video.DoesNotExist:
        logger.error(f'Video {video_id} no existe')
        raise
    
    except ThumbnailGenerationError as e:
        logger.error(f'Error al generar miniatura del video {video_id}: {str(e)}')
        raise self.retry(exc=e, countdown=30 * (self.request.retries + 1))
    
    except Exception as e:
        logger.error(f'Error inesperado al generar miniatura del video {video_id}: {str(e)}')
        raise


@shared_task
def mover_video_a_media_task(video_id: int, temp_video_path: str):
    """
    Tarea para mover el video de la carpeta temporal a media
    
    Args:
        video_id: ID del video
        temp_video_path: Ruta temporal del video
    
    Returns:
        str: Ruta final del video en media
    """
    try:
        logger.info(f'Moviendo video {video_id} a carpeta media')
        
        from django.core.files import File
        from django.conf import settings
        import shutil
        
        video = Video.objects.get(id=video_id)
        temp_path = Path(temp_video_path)
        
        if not temp_path.exists():
            raise FileNotFoundError(f'Archivo temporal no existe: {temp_path}')
        
        # Definir ruta en media
        media_dir = settings.MEDIA_ROOT / 'videos' / str(timezone.now().year) / str(timezone.now().month)
        media_dir.mkdir(parents=True, exist_ok=True)
        
        final_path = media_dir / f'video_{video_id}{temp_path.suffix}'
        
        # Mover archivo
        shutil.move(str(temp_path), str(final_path))
        
        # Actualizar modelo con la ruta del archivo
        with open(final_path, 'rb') as f:
            video.ruta_video_completo.save(
                final_path.name,
                File(f),
                save=True
            )
        
        logger.info(f'Video {video_id} movido a: {final_path}')
        
        return str(final_path)
    
    except Exception as e:
        logger.error(f'Error al mover video {video_id}: {str(e)}')
        raise


@shared_task
def finalizar_procesamiento_task(video_id: int):
    """
    Tarea para finalizar el procesamiento del video
    
    Args:
        video_id: ID del video
    """
    try:
        logger.info(f'Finalizando procesamiento del video {video_id}')
        
        video = Video.objects.get(id=video_id)
        
        # Actualizar estado y fecha de procesamiento
        video.estado = 'completado'
        video.fecha_procesamiento = timezone.now()
        video.save()
        
        # Crear log final
        LogProcesamiento.objects.create(
            video=video,
            etapa='finalizacion',
            estado='completado',
            mensaje='Procesamiento completado exitosamente'
        )
        
        logger.info(f'Procesamiento del video {video_id} completado')
    
    except Video.DoesNotExist:
        logger.error(f'Video {video_id} no existe')
        raise
    
    except Exception as e:
        logger.error(f'Error al finalizar procesamiento del video {video_id}: {str(e)}')
        raise


@shared_task
def limpiar_archivos_temporales_task():
    """
    Tarea programada para limpiar archivos temporales antiguos
    """
    try:
        logger.info('Iniciando limpieza de archivos temporales')
        
        cleaner = FileCleaner()
        result = cleaner.clean_old_files()
        
        logger.info(
            f'Limpieza completada: {result["deleted_count"]} archivos, '
            f'{result["freed_space_mb"]} MB liberados'
        )
        
        return result
    
    except Exception as e:
        logger.error(f'Error en limpieza de archivos temporales: {str(e)}')
        raise


@shared_task
def procesar_video_completo_task(video_id: int):
    """
    Pipeline COMPLETO: 
    Descarga → Audio → Transcripción → Análisis → Segmentación → Finalizar
    
    Args:
        video_id: ID del video a procesar
    """
    try:
        logger.info(f'Iniciando procesamiento COMPLETO del video {video_id}')
        
        # Crear cadena de tareas
        workflow = chain(
            # 1. Descargar video
            descargar_video_task.s(video_id),
            # 2. En paralelo: [Audio → Transcripción → Análisis] | Miniatura
            group(
                chain(
                    # 2a. Extraer audio
                    extraer_audio_task.s(video_id),
                    # 2b. Transcribir audio
                    transcribir_audio_task.s(video_id),
                    # 2c. Analizar con IA
                    analizar_video_task.si(video_id)
                ),
                # 2d. Generar miniatura (en paralelo)
                generar_miniatura_task.s(video_id)
            ),
            # 3. Segmentar video en clips
            segmentar_video_task.s(video_id),
            # 4. Mover video completo a media
            mover_video_a_media_task.s(video_id),
            # 5. Finalizar procesamiento
            finalizar_procesamiento_task.si(video_id)
        )
        
        # Ejecutar workflow
        result = workflow.apply_async()
        
        logger.info(f'Workflow COMPLETO iniciado para video {video_id}: {result.id}')
        
        return result.id
    
    except Exception as e:
        logger.error(f'Error al iniciar procesamiento del video {video_id}: {str(e)}')
        
        try:
            video = Video.objects.get(id=video_id)
            video.estado = 'error'
            video.save()
        except:
            pass
        
        raise

@shared_task(bind=True)
def test_task(self, seconds: int = 5):
    """
    Tarea de prueba para verificar que Celery funciona
    
    Args:
        seconds: Segundos a esperar
    
    Returns:
        str: Mensaje de éxito
    """
    import time
    
    logger.info(f'Tarea de prueba iniciada, esperando {seconds} segundos')
    
    for i in range(seconds):
        time.sleep(1)
        logger.info(f'Segundo {i+1}/{seconds}')
    
    logger.info('Tarea de prueba completada')
    
    return f'Tarea completada después de {seconds} segundos'



@shared_task(bind=True, max_retries=2)
def transcribir_audio_task(self, video_id: int, audio_path: str):
    """
    Tarea asíncrona para transcribir audio
    
    Args:
        video_id: ID del video
        audio_path: Ruta del archivo de audio
    
    Returns:
        dict: Datos de la transcripción
    """
    try:
        logger.info(f'Iniciando transcripción del video {video_id}')
        
        # Obtener video
        video = Video.objects.get(id=video_id)
        
        # Actualizar estado
        video.estado = 'transcribiendo'
        video.save()
        
        # Transcribir
        service = TranscriptionService(video)
        result = service.transcribe(Path(audio_path))
        
        logger.info(f'Transcripción completada para video {video_id}')
        
        return {
            'video_id': video_id,
            'idioma': result['idioma'],
            'precision': result['precision_estimada'],
            'palabras': len(result['contenido_completo'].split())
        }
    
    except Video.DoesNotExist:
        logger.error(f'Video {video_id} no existe')
        raise
    
    except TranscriptionError as e:
        logger.error(f'Error al transcribir video {video_id}: {str(e)}')
        
        try:
            video = Video.objects.get(id=video_id)
            video.estado = 'error'
            video.save()
        except:
            pass
        
        # Reintentar si no se han agotado los intentos
        raise self.retry(exc=e, countdown=120 * (self.request.retries + 1))
    
    except Exception as e:
        logger.error(f'Error inesperado al transcribir video {video_id}: {str(e)}')
        
        try:
            video = Video.objects.get(id=video_id)
            video.estado = 'error'
            video.save()
        except:
            pass
        
        raise

@shared_task(bind=True, max_retries=2)
def analizar_video_task(self, video_id: int):
    """
    Tarea asíncrona para analizar video con IA
    
    Args:
        video_id: ID del video
    
    Returns:
        dict: Resultado del análisis
    """
    try:
        logger.info(f'Iniciando análisis IA del video {video_id}')
        
        # Obtener video
        video = Video.objects.get(id=video_id)
        
        # Actualizar estado
        video.estado = 'analizando'
        video.save()
        
        # Analizar
        service = AnalysisService(video)
        result = service.analyze()
        
        # Guardar segmentos importantes identificados
        segmentos_guardados = 0
        for i, seg_data in enumerate(result['segmentos_importantes'], 1):
            Segmento.objects.create(
                video=video,
                titulo=seg_data['titulo'],
                descripcion=seg_data['descripcion'],
                timestamp_inicio_seg=seg_data['timestamp_inicio'],
                timestamp_fin_seg=seg_data['timestamp_fin'],
                duracion_seg=seg_data['duracion'],
                orden=i,
                relevancia_score=seg_data['relevancia'],
                tipo_contenido=seg_data['tipo']
            )
            segmentos_guardados += 1
        
        logger.info(f'Análisis completado para video {video_id}. {segmentos_guardados} segmentos guardados')
        
        return {
            'video_id': video_id,
            'segmentos_identificados': segmentos_guardados,
            'resumen_generado': True
        }
    
    except Video.DoesNotExist:
        logger.error(f'Video {video_id} no existe')
        raise
    
    except AnalysisError as e:
        logger.error(f'Error al analizar video {video_id}: {str(e)}')
        
        try:
            video = Video.objects.get(id=video_id)
            video.estado = 'error'
            video.save()
        except:
            pass
        
        # Reintentar
        raise self.retry(exc=e, countdown=180 * (self.request.retries + 1))
    
    except Exception as e:
        logger.error(f'Error inesperado al analizar video {video_id}: {str(e)}')
        
        try:
            video = Video.objects.get(id=video_id)
            video.estado = 'error'
            video.save()
        except:
            pass
        
        raise

@shared_task(bind=True, max_retries=2)
def segmentar_video_task(self, video_id: int, video_path: str):
    """
    Tarea asíncrona para segmentar video
    
    Args:
        video_id: ID del video
        video_path: Ruta del video completo
    
    Returns:
        dict: Resultado de la segmentación
    """
    try:
        logger.info(f'Iniciando segmentación del video {video_id}')
        
        # Obtener video
        video = Video.objects.get(id=video_id)
        
        # Actualizar estado
        video.estado = 'segmentando'
        video.save()
        
        # Segmentar
        service = VideoSegmentationService(video)
        segmentos = service.segment_video(Path(video_path))
        
        logger.info(f'Segmentación completada para video {video_id}. {len(segmentos)} segmentos')
        
        return {
            'video_id': video_id,
            'segmentos_procesados': len(segmentos),
            'segmentos': [
                {
                    'id': seg['segmento_id'],
                    'titulo': seg['titulo'],
                    'duracion': seg['duracion']
                }
                for seg in segmentos
            ]
        }
    
    except Video.DoesNotExist:
        logger.error(f'Video {video_id} no existe')
        raise
    
    except SegmentationError as e:
        logger.error(f'Error al segmentar video {video_id}: {str(e)}')
        
        try:
            video = Video.objects.get(id=video_id)
            video.estado = 'error'
            video.save()
        except:
            pass
        
        # Reintentar
        raise self.retry(exc=e, countdown=120 * (self.request.retries + 1))
    
    except Exception as e:
        logger.error(f'Error inesperado al segmentar video {video_id}: {str(e)}')
        
        try:
            video = Video.objects.get(id=video_id)
            video.estado = 'error'
            video.save()
        except:
            pass
        
        raise
