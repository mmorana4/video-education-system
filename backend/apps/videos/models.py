from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, FileExtensionValidator

class Video(models.Model):
    """
    Modelo para almacenar información de videos subidos
    """
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('descargando', 'Descargando'),
        ('procesando', 'Procesando'),
        ('transcribiendo', 'Transcribiendo'),
        ('analizando', 'Analizando IA'),
        ('segmentando', 'Segmentando'),
        ('completado', 'Completado'),
        ('error', 'Error'),
    ]
    
    FUENTE_CHOICES = [
        ('youtube', 'YouTube'),
        ('vimeo', 'Vimeo'),
        ('local', 'Archivo Local'),
        ('otro', 'Otro'),
    ]
    
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='videos',
        verbose_name='Usuario'
    )
    titulo = models.CharField(
        'Título',
        max_length=255
    )
    url_original = models.URLField(
        'URL Original',
        max_length=500,
        null=True,
        blank=True
    )
    fuente = models.CharField(
        'Fuente',
        max_length=20,
        choices=FUENTE_CHOICES
    )
    ruta_video_completo = models.FileField(
        'Video Completo',
        upload_to='videos/%Y/%m/%d/',
        null=True,
        blank=True
    )
    duracion_segundos = models.IntegerField(
        'Duración (segundos)',
        validators=[MinValueValidator(0)],
        null=True,
        blank=True
    )
    formato = models.CharField(
        'Formato',
        max_length=10,
        null=True,
        blank=True
    )
    tamano_mb = models.FloatField(
        'Tamaño (MB)',
        validators=[MinValueValidator(0)],
        null=True,
        blank=True
    )
    estado = models.CharField(
        'Estado',
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente'
    )
    fecha_subida = models.DateTimeField(
        'Fecha de Subida',
        auto_now_add=True
    )
    fecha_procesamiento = models.DateTimeField(
        'Fecha de Procesamiento',
        null=True,
        blank=True
    )
    miniatura_url = models.ImageField(
        'Miniatura',
        upload_to='miniaturas/%Y/%m/%d/',
        null=True,
        blank=True
    )
    metadata_json = models.JSONField(
        'Metadata',
        null=True,
        blank=True,
        help_text='Información adicional en formato JSON'
    )
    
    class Meta:
        db_table = 'videos'
        verbose_name = 'Video'
        verbose_name_plural = 'Videos'
        ordering = ['-fecha_subida']
        indexes = [
            models.Index(fields=['usuario', 'estado']),
            models.Index(fields=['fecha_subida']),
        ]
    
    def __str__(self):
        return f"{self.titulo} - {self.usuario.username}"
    
    @property
    def duracion_formateada(self):
        """Retorna la duración en formato HH:MM:SS"""
        if self.duracion_segundos:
            horas = self.duracion_segundos // 3600
            minutos = (self.duracion_segundos % 3600) // 60
            segundos = self.duracion_segundos % 60
            return f"{horas:02d}:{minutos:02d}:{segundos:02d}"
        return "00:00:00"


class Transcripcion(models.Model):
    """
    Modelo para almacenar transcripciones de videos
    """
    video = models.OneToOneField(
        Video,
        on_delete=models.CASCADE,
        related_name='transcripcion',
        verbose_name='Video'
    )
    contenido_completo = models.TextField(
        'Contenido Completo',
        help_text='Transcripción completa del audio'
    )
    idioma_detectado = models.CharField(
        'Idioma Detectado',
        max_length=10,
        default='es'
    )
    precision_estimada = models.FloatField(
        'Precisión Estimada',
        validators=[MinValueValidator(0), MinValueValidator(100)],
        null=True,
        blank=True,
        help_text='Porcentaje de precisión de la transcripción'
    )
    transcripcion_con_timestamps = models.JSONField(
        'Transcripción con Timestamps',
        help_text='Transcripción segmentada con marcas de tiempo'
    )
    fecha_generacion = models.DateTimeField(
        'Fecha de Generación',
        auto_now_add=True
    )
    modelo_utilizado = models.CharField(
        'Modelo Utilizado',
        max_length=100,
        help_text='Nombre del modelo de transcripción usado'
    )
    
    class Meta:
        db_table = 'transcripciones'
        verbose_name = 'Transcripción'
        verbose_name_plural = 'Transcripciones'
        ordering = ['-fecha_generacion']
    
    def __str__(self):
        return f"Transcripción de: {self.video.titulo}"


class ResumenEjecutivo(models.Model):
    """
    Modelo para almacenar resúmenes ejecutivos generados por IA
    """
    video = models.OneToOneField(
        Video,
        on_delete=models.CASCADE,
        related_name='resumen_ejecutivo',
        verbose_name='Video'
    )
    resumen_completo = models.TextField(
        'Resumen Completo',
        help_text='Resumen ejecutivo del contenido del video'
    )
    temas_principales = models.TextField(
        'Temas Principales',
        help_text='Lista de temas principales identificados'
    )
    conclusiones_clave = models.TextField(
        'Conclusiones Clave',
        help_text='Conclusiones más importantes'
    )
    puntos_importantes = models.TextField(
        'Puntos Importantes',
        help_text='Puntos destacados del contenido'
    )
    cantidad_palabras = models.IntegerField(
        'Cantidad de Palabras',
        validators=[MinValueValidator(0)],
        null=True,
        blank=True
    )
    fecha_generacion = models.DateTimeField(
        'Fecha de Generación',
        auto_now_add=True
    )
    modelo_ia_utilizado = models.CharField(
        'Modelo IA Utilizado',
        max_length=100,
        help_text='Nombre del modelo de IA usado para el resumen'
    )
    
    class Meta:
        db_table = 'resumenes_ejecutivos'
        verbose_name = 'Resumen Ejecutivo'
        verbose_name_plural = 'Resúmenes Ejecutivos'
        ordering = ['-fecha_generacion']
    
    def __str__(self):
        return f"Resumen de: {self.video.titulo}"


class Segmento(models.Model):
    """
    Modelo para almacenar segmentos importantes del video
    """
    TIPO_CONTENIDO_CHOICES = [
        ('introduccion', 'Introducción'),
        ('concepto_clave', 'Concepto Clave'),
        ('ejemplo', 'Ejemplo'),
        ('demostracion', 'Demostración'),
        ('conclusion', 'Conclusión'),
        ('pregunta_respuesta', 'Pregunta y Respuesta'),
        ('ejercicio', 'Ejercicio'),
        ('otro', 'Otro'),
    ]
    
    video = models.ForeignKey(
        Video,
        on_delete=models.CASCADE,
        related_name='segmentos',
        verbose_name='Video'
    )
    titulo = models.CharField(
        'Título',
        max_length=255
    )
    descripcion = models.TextField(
        'Descripción',
        help_text='Descripción del contenido del segmento'
    )
    timestamp_inicio_seg = models.IntegerField(
        'Timestamp Inicio (segundos)',
        validators=[MinValueValidator(0)],
        help_text='Segundo de inicio del segmento'
    )
    timestamp_fin_seg = models.IntegerField(
        'Timestamp Fin (segundos)',
        validators=[MinValueValidator(0)],
        help_text='Segundo de fin del segmento'
    )
    duracion_seg = models.IntegerField(
        'Duración (segundos)',
        validators=[MinValueValidator(0)]
    )
    ruta_archivo_segmento = models.FileField(
        'Archivo del Segmento',
        upload_to='segmentos/%Y/%m/%d/',
        null=True,
        blank=True
    )
    orden = models.IntegerField(
        'Orden',
        validators=[MinValueValidator(1)],
        help_text='Orden de importancia del segmento'
    )
    relevancia_score = models.FloatField(
        'Score de Relevancia',
        validators=[MinValueValidator(0), MinValueValidator(10)],
        help_text='Puntuación de relevancia (0-10)'
    )
    tipo_contenido = models.CharField(
        'Tipo de Contenido',
        max_length=30,
        choices=TIPO_CONTENIDO_CHOICES,
        default='otro'
    )
    fecha_creacion = models.DateTimeField(
        'Fecha de Creación',
        auto_now_add=True
    )
    miniatura_url = models.ImageField(
        'Miniatura',
        upload_to='miniaturas_segmentos/%Y/%m/%d/',
        null=True,
        blank=True
    )
    
    class Meta:
        db_table = 'segmentos'
        verbose_name = 'Segmento'
        verbose_name_plural = 'Segmentos'
        ordering = ['video', 'orden']
        indexes = [
            models.Index(fields=['video', 'orden']),
            models.Index(fields=['relevancia_score']),
        ]
    
    def __str__(self):
        return f"{self.titulo} ({self.timestamp_inicio_seg}s - {self.timestamp_fin_seg}s)"
    
    @property
    def timestamp_inicio_formateado(self):
        """Retorna el timestamp de inicio en formato MM:SS"""
        minutos = self.timestamp_inicio_seg // 60
        segundos = self.timestamp_inicio_seg % 60
        return f"{minutos:02d}:{segundos:02d}"
    
    @property
    def timestamp_fin_formateado(self):
        """Retorna el timestamp de fin en formato MM:SS"""
        minutos = self.timestamp_fin_seg // 60
        segundos = self.timestamp_fin_seg % 60
        return f"{minutos:02d}:{segundos:02d}"


class EtiquetaVideo(models.Model):
    """
    Modelo para etiquetar y categorizar videos
    """
    video = models.ForeignKey(
        Video,
        on_delete=models.CASCADE,
        related_name='etiquetas',
        verbose_name='Video'
    )
    etiqueta = models.CharField(
        'Etiqueta',
        max_length=50
    )
    categoria = models.CharField(
        'Categoría',
        max_length=50,
        null=True,
        blank=True
    )
    fecha_asignacion = models.DateTimeField(
        'Fecha de Asignación',
        auto_now_add=True
    )
    
    class Meta:
        db_table = 'etiquetas_video'
        verbose_name = 'Etiqueta de Video'
        verbose_name_plural = 'Etiquetas de Videos'
        ordering = ['video', 'etiqueta']
        unique_together = ['video', 'etiqueta']
    
    def __str__(self):
        return f"{self.etiqueta} - {self.video.titulo}"


class EtiquetaSegmento(models.Model):
    """
    Modelo para etiquetar segmentos específicos
    """
    segmento = models.ForeignKey(
        Segmento,
        on_delete=models.CASCADE,
        related_name='etiquetas',
        verbose_name='Segmento'
    )
    etiqueta = models.CharField(
        'Etiqueta',
        max_length=50
    )
    confianza = models.FloatField(
        'Confianza',
        validators=[MinValueValidator(0), MinValueValidator(1)],
        help_text='Nivel de confianza de la etiqueta (0-1)'
    )
    fecha_asignacion = models.DateTimeField(
        'Fecha de Asignación',
        auto_now_add=True
    )
    
    class Meta:
        db_table = 'etiquetas_segmento'
        verbose_name = 'Etiqueta de Segmento'
        verbose_name_plural = 'Etiquetas de Segmentos'
        ordering = ['segmento', '-confianza']
    
    def __str__(self):
        return f"{self.etiqueta} ({self.confianza:.2f}) - {self.segmento.titulo}"


class LogProcesamiento(models.Model):
    """
    Modelo para registrar logs del procesamiento de videos
    """
    ESTADO_CHOICES = [
        ('iniciado', 'Iniciado'),
        ('en_progreso', 'En Progreso'),
        ('completado', 'Completado'),
        ('error', 'Error'),
        ('cancelado', 'Cancelado'),
    ]
    
    video = models.ForeignKey(
        Video,
        on_delete=models.CASCADE,
        related_name='logs',
        verbose_name='Video'
    )
    etapa = models.CharField(
        'Etapa',
        max_length=50,
        help_text='Nombre de la etapa del procesamiento'
    )
    estado = models.CharField(
        'Estado',
        max_length=20,
        choices=ESTADO_CHOICES
    )
    mensaje = models.TextField(
        'Mensaje',
        help_text='Mensaje descriptivo del log'
    )
    error_detalle = models.TextField(
        'Detalle del Error',
        null=True,
        blank=True,
        help_text='Información detallada del error si existe'
    )
    timestamp = models.DateTimeField(
        'Timestamp',
        auto_now_add=True
    )
    duracion_ms = models.IntegerField(
        'Duración (ms)',
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        help_text='Duración de la etapa en milisegundos'
    )
    
    class Meta:
        db_table = 'logs_procesamiento'
        verbose_name = 'Log de Procesamiento'
        verbose_name_plural = 'Logs de Procesamiento'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['video', 'timestamp']),
            models.Index(fields=['estado']),
        ]
    
    def __str__(self):
        return f"{self.video.titulo} - {self.etapa} ({self.estado})"


class ConfiguracionSistema(models.Model):
    """
    Modelo para configuraciones del sistema
    """
    parametro = models.CharField(
        'Parámetro',
        max_length=100,
        unique=True
    )
    valor = models.TextField(
        'Valor'
    )
    descripcion = models.TextField(
        'Descripción',
        help_text='Descripción del parámetro de configuración'
    )
    fecha_modificacion = models.DateTimeField(
        'Fecha de Modificación',
        auto_now=True
    )
    modificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='configuraciones_modificadas',
        verbose_name='Modificado Por'
    )
    
    class Meta:
        db_table = 'configuracion_sistema'
        verbose_name = 'Configuración del Sistema'
        verbose_name_plural = 'Configuraciones del Sistema'
        ordering = ['parametro']
    
    def __str__(self):
        return f"{self.parametro}: {self.valor[:50]}"