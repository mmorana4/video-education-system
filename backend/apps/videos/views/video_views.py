from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from apps.videos.services import VideoDownloader, VideoDownloadError
from apps.videos.models import Video, Segmento, Transcripcion, ResumenEjecutivo
from apps.videos.serializers import (
    VideoListSerializer,
    VideoDetailSerializer,
    VideoCreateSerializer,
    VideoUpdateSerializer,
    VideoCompleteSerializer,
    SegmentoListSerializer,
    SegmentoDetailSerializer,
    TranscripcionSerializer,
    ResumenEjecutivoSerializer,
)
from apps.users.permissions import IsOwnerOrAdmin, IsDocenteOrAdmin
from apps.videos.tasks.tasks import procesar_video_completo_task,logger,analizar_video_task,segmentar_video_task
from django.http import FileResponse, Http404

class VideoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD de videos
    
    list: GET /api/videos/
    create: POST /api/videos/
    retrieve: GET /api/videos/{id}/
    update: PUT /api/videos/{id}/
    partial_update: PATCH /api/videos/{id}/
    destroy: DELETE /api/videos/{id}/
    """
    permission_classes = [IsAuthenticated, IsDocenteOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['estado', 'fuente', 'usuario']
    search_fields = ['titulo', 'metadata_json']
    ordering_fields = ['fecha_subida', 'duracion_segundos', 'titulo']
    ordering = ['-fecha_subida']
    
    def get_queryset(self):
        """
        Filtrar videos según el usuario
        - Admin ve todos los videos
        - Docente solo ve sus propios videos
        """
        user = self.request.user
        if user.rol == 'admin':
            return Video.objects.all().select_related('usuario')
        return Video.objects.filter(usuario=user).select_related('usuario')
    
    def get_serializer_class(self):
        """Retornar serializer según la acción"""
        if self.action == 'list':
            return VideoListSerializer
        elif self.action == 'create':
            return VideoCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return VideoUpdateSerializer
        elif self.action == 'completo':
            return VideoCompleteSerializer
        return VideoDetailSerializer
    
    def get_permissions(self):
        """Permisos específicos por acción"""
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwnerOrAdmin()]
        return super().get_permissions()
    
    def perform_create(self, serializer):
        """Crear video asignando el usuario autenticado"""
        serializer.save(usuario=self.request.user)
    
    @action(detail=True, methods=['get'])
    def completo(self, request, pk=None):
        """
        Endpoint para obtener video con todas sus relaciones
        GET /api/videos/{id}/completo/
        """
        video = self.get_object()
        serializer = VideoCompleteSerializer(video)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def segmentos(self, request, pk=None):
        """
        Obtener todos los segmentos de un video
        GET /api/videos/{id}/segmentos/
        """
        video = self.get_object()
        segmentos = video.segmentos.all().order_by('orden')
        serializer = SegmentoListSerializer(segmentos, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def transcripcion(self, request, pk=None):
        """
        Obtener la transcripción de un video
        GET /api/videos/{id}/transcripcion/
        """
        video = self.get_object()
        try:
            serializer = TranscripcionSerializer(video.transcripcion)
            return Response(serializer.data)
        except Transcripcion.DoesNotExist:
            return Response(
                {'detail': 'Este video no tiene transcripción.'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get'])
    def resumen(self, request, pk=None):
        """
        Obtener el resumen ejecutivo de un video
        GET /api/videos/{id}/resumen/
        """
        video = self.get_object()
        try:
            serializer = ResumenEjecutivoSerializer(video.resumen_ejecutivo)
            return Response(serializer.data)
        except ResumenEjecutivo.DoesNotExist:
            return Response(
                {'detail': 'Este video no tiene resumen ejecutivo.'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        Obtener estadísticas de videos del usuario
        GET /api/videos/estadisticas/
        """
        queryset = self.get_queryset()
        
        stats = {
            'total_videos': queryset.count(),
            'por_estado': {},
            'por_fuente': {},
            'duracion_total_segundos': 0,
            'duracion_total_formateada': '00:00:00'
        }
        
        # Contar por estado
        for estado, _ in Video.ESTADO_CHOICES:
            count = queryset.filter(estado=estado).count()
            stats['por_estado'][estado] = count
        
        # Contar por fuente
        for fuente, _ in Video.FUENTE_CHOICES:
            count = queryset.filter(fuente=fuente).count()
            stats['por_fuente'][fuente] = count
        
        # Calcular duración total
        total_segundos = sum(
            v.duracion_segundos for v in queryset if v.duracion_segundos
        )
        stats['duracion_total_segundos'] = total_segundos
        
        # Formatear duración total
        horas = total_segundos // 3600
        minutos = (total_segundos % 3600) // 60
        segundos = total_segundos % 60
        stats['duracion_total_formateada'] = f"{horas:02d}:{minutos:02d}:{segundos:02d}"
        
        return Response(stats)
    
#crear vistas para segmento

class SegmentoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD de segmentos
    
    list: GET /api/segmentos/
    create: POST /api/segmentos/
    retrieve: GET /api/segmentos/{id}/
    update: PUT /api/segmentos/{id}/
    partial_update: PATCH /api/segmentos/{id}/
    destroy: DELETE /api/segmentos/{id}/
    """
    permission_classes = [IsAuthenticated, IsDocenteOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['video', 'tipo_contenido']
    search_fields = ['titulo', 'descripcion']
    ordering_fields = ['orden', 'relevancia_score', 'duracion_seg']
    ordering = ['orden']
    
    def get_queryset(self):
        """
        Filtrar segmentos según el usuario
        """
        user = self.request.user
        if user.rol == 'admin':
            return Segmento.objects.all().select_related('video', 'video__usuario')
        return Segmento.objects.filter(
            video__usuario=user
        ).select_related('video', 'video__usuario')
    
    def get_serializer_class(self):
        """Retornar serializer según la acción"""
        if self.action == 'list':
            return SegmentoListSerializer
        return SegmentoDetailSerializer
    
    @action(detail=False, methods=['get'])
    def mas_relevantes(self, request):
        """
        Obtener los segmentos más relevantes
        GET /api/segmentos/mas_relevantes/?limit=10
        """
        limit = int(request.query_params.get('limit', 10))
        segmentos = self.get_queryset().order_by('-relevancia_score')[:limit]
        serializer = self.get_serializer(segmentos, many=True)
        return Response(serializer.data)
    
#crear vistas para transcripcion y resumen ejecutivo si es necesario

class TranscripcionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD de transcripciones
    """
    permission_classes = [IsAuthenticated, IsDocenteOrAdmin]
    serializer_class = TranscripcionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['video', 'idioma_detectado']
    search_fields = ['contenido_completo']
    
    def get_queryset(self):
        """Filtrar transcripciones según el usuario"""
        user = self.request.user
        if user.rol == 'admin':
            return Transcripcion.objects.all().select_related('video', 'video__usuario')
        return Transcripcion.objects.filter(
            video__usuario=user
        ).select_related('video', 'video__usuario')


class ResumenEjecutivoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para CRUD de resúmenes ejecutivos
    """
    permission_classes = [IsAuthenticated, IsDocenteOrAdmin]
    serializer_class = ResumenEjecutivoSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['video']
    search_fields = ['resumen_completo', 'temas_principales', 'conclusiones_clave']
    
    def get_queryset(self):
        """Filtrar resúmenes según el usuario"""
        user = self.request.user
        if user.rol == 'admin':
            return ResumenEjecutivo.objects.all().select_related('video', 'video__usuario')
        return ResumenEjecutivo.objects.filter(
            video__usuario=user
        ).select_related('video', 'video__usuario')
    
# Agregar al VideoViewSet:

@action(detail=False, methods=['post'])
def validar_url(self, request):
    """
    Validar URL de video antes de crear
    POST /api/videos/videos/validar_url/
    
    Body: {"url": "https://youtube.com/..."}
    """
    url = request.data.get('url')
    
    if not url:
        return Response(
            {'error': 'URL es requerida'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Crear video temporal para validar
    temp_video = Video(url_original=url)
    downloader = VideoDownloader(temp_video)
    
    is_valid, message = downloader.validate_url(url)
    
    if is_valid:
        # Obtener información del video
        info = downloader.get_video_info(url)
        
        return Response({
            'valid': True,
            'message': message,
            'info': info
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'valid': False,
            'message': message
        }, status=status.HTTP_400_BAD_REQUEST)



@action(detail=True, methods=['post'])
def procesar(self, request, pk=None):
    """
    Iniciar procesamiento asíncrono de un video
    POST /api/videos/videos/{id}/procesar/
    """
    video = self.get_object()
    
    # Verificar que el video esté en estado pendiente
    if video.estado != 'pendiente':
        return Response(
            {'error': f'El video está en estado "{video.estado}" y no puede ser procesado'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verificar que tenga URL
    if not video.url_original:
        return Response(
            {'error': 'El video no tiene URL para procesar'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Iniciar tarea asíncrona
        task = procesar_video_completo_task.delay(video.id)
        
        # Actualizar estado
        video.estado = 'procesando'
        video.save()
        
        return Response({
            'message': 'Procesamiento iniciado',
            'video_id': video.id,
            'task_id': task.id,
            'estado': video.estado
        }, status=status.HTTP_202_ACCEPTED)
    
    except Exception as e:
        logger.error(f'Error al iniciar procesamiento: {str(e)}')
        return Response(
            {'error': f'Error al iniciar procesamiento: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@action(detail=True, methods=['get'])
def estado_procesamiento(self, request, pk=None):
    """
    Obtener estado del procesamiento de un video
    GET /api/videos/videos/{id}/estado_procesamiento/
    """
    video = self.get_object()
    
    # Obtener logs de procesamiento
    logs = video.logs.all().order_by('-timestamp')[:10]
    
    logs_data = [{
        'etapa': log.etapa,
        'estado': log.estado,
        'mensaje': log.mensaje,
        'timestamp': log.timestamp,
        'duracion_ms': log.duracion_ms
    } for log in logs]
    
    return Response({
        'video_id': video.id,
        'titulo': video.titulo,
        'estado': video.estado,
        'fecha_subida': video.fecha_subida,
        'fecha_procesamiento': video.fecha_procesamiento,
        'logs': logs_data
    }, status=status.HTTP_200_OK)

@action(detail=True, methods=['post'])
def reanalizar(self, request, pk=None):
    """
    Re-analizar un video con IA
    POST /api/videos/videos/{id}/reanalizar/
    """
    video = self.get_object()
    
    # Verificar que tenga transcripción
    if not hasattr(video, 'transcripcion'):
        return Response(
            {'error': 'El video no tiene transcripción. Transcríbalo primero.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Iniciar tarea de análisis
        task = analizar_video_task.delay(video.id)
        
        return Response({
            'message': 'Re-análisis iniciado',
            'video_id': video.id,
            'task_id': task.id
        }, status=status.HTTP_202_ACCEPTED)
    
    except Exception as e:
        logger.error(f'Error al iniciar re-análisis: {str(e)}')
        return Response(
            {'error': f'Error al iniciar re-análisis: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@action(detail=True, methods=['post'])
def resegmentar(self, request, pk=None):
    """
    Re-segmentar un video
    POST /api/videos/videos/{id}/resegmentar/
    """
    video = self.get_object()
    
    # Verificar que tenga segmentos identificados
    if not video.segmentos.exists():
        return Response(
            {'error': 'El video no tiene segmentos identificados. Analice el video primero.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verificar que tenga archivo
    if not video.ruta_video_completo:
        return Response(
            {'error': 'El video no tiene archivo. Procese el video primero.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Iniciar tarea de segmentación
        task = segmentar_video_task.delay(
            video.id,
            str(video.ruta_video_completo.path)
        )
        
        return Response({
            'message': 'Re-segmentación iniciada',
            'video_id': video.id,
            'task_id': task.id,
            'segmentos_a_procesar': video.segmentos.count()
        }, status=status.HTTP_202_ACCEPTED)
    
    except Exception as e:
        logger.error(f'Error al iniciar re-segmentación: {str(e)}')
        return Response(
            {'error': f'Error al iniciar re-segmentación: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@action(detail=True, methods=['get'])
def descargar_segmento(self, request, pk=None):
    """
    Obtener URL de descarga de un segmento específico
    GET /api/videos/segmentos/{id}/descargar/
    
    Nota: Este endpoint va en SegmentoViewSet
    """
    # Se implementará en SegmentoViewSet
    pass
@action(detail=True, methods=['get'])
def descargar(self, request, pk=None):
    """
    Descargar archivo de segmento
    GET /api/videos/segmentos/{id}/descargar/
    """
    segmento = self.get_object()
    
    # Verificar que tenga archivo
    if not segmento.ruta_archivo_segmento:
        raise Http404("Segmento sin archivo. Re-segmente el video.")
    
    try:
        # Retornar archivo
        response = FileResponse(
            segmento.ruta_archivo_segmento.open('rb'),
            content_type='video/mp4'
        )
        response['Content-Disposition'] = f'attachment; filename="{segmento.titulo}.mp4"'
        
        return response
    
    except Exception as e:
        logger.error(f'Error al descargar segmento: {str(e)}')
        return Response(
            {'error': 'Error al descargar segmento'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )