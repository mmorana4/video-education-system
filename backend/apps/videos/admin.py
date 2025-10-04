from django.contrib import admin
from .models import (
    Video, Transcripcion, ResumenEjecutivo, Segmento,
    EtiquetaVideo, EtiquetaSegmento, LogProcesamiento,
    ConfiguracionSistema
)

class EtiquetaVideoInline(admin.TabularInline):
    model = EtiquetaVideo
    extra = 1

class SegmentoInline(admin.TabularInline):
    model = Segmento
    extra = 0
    fields = ('titulo', 'timestamp_inicio_seg', 'timestamp_fin_seg', 'orden', 'relevancia_score')
    readonly_fields = ('fecha_creacion',)

class LogProcesamientoInline(admin.TabularInline):
    model = LogProcesamiento
    extra = 0
    readonly_fields = ('timestamp',)
    can_delete = False

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'usuario', 'fuente', 'estado', 'duracion_formateada', 'fecha_subida')
    list_filter = ('estado', 'fuente', 'fecha_subida')
    search_fields = ('titulo', 'usuario__username', 'usuario__email')
    readonly_fields = ('fecha_subida', 'fecha_procesamiento', 'duracion_formateada')
    date_hierarchy = 'fecha_subida'
    inlines = [EtiquetaVideoInline, SegmentoInline, LogProcesamientoInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('usuario', 'titulo', 'fuente', 'url_original')
        }),
        ('Archivo', {
            'fields': ('ruta_video_completo', 'miniatura_url', 'formato', 'tamano_mb')
        }),
        ('Estado y Procesamiento', {
            'fields': ('estado', 'duracion_segundos', 'duracion_formateada', 'fecha_subida', 'fecha_procesamiento')
        }),
        ('Metadata', {
            'fields': ('metadata_json',),
            'classes': ('collapse',)
        }),
    )

@admin.register(Transcripcion)
class TranscripcionAdmin(admin.ModelAdmin):
    list_display = ('video', 'idioma_detectado', 'precision_estimada', 'modelo_utilizado', 'fecha_generacion')
    list_filter = ('idioma_detectado', 'fecha_generacion')
    search_fields = ('video__titulo', 'contenido_completo')
    readonly_fields = ('fecha_generacion',)
    
    fieldsets = (
        ('Video', {
            'fields': ('video',)
        }),
        ('Transcripción', {
            'fields': ('contenido_completo', 'transcripcion_con_timestamps')
        }),
        ('Metadata', {
            'fields': ('idioma_detectado', 'precision_estimada', 'modelo_utilizado', 'fecha_generacion')
        }),
    )

@admin.register(ResumenEjecutivo)
class ResumenEjecutivoAdmin(admin.ModelAdmin):
    list_display = ('video', 'cantidad_palabras', 'modelo_ia_utilizado', 'fecha_generacion')
    list_filter = ('fecha_generacion', 'modelo_ia_utilizado')
    search_fields = ('video__titulo', 'resumen_completo', 'temas_principales')
    readonly_fields = ('fecha_generacion',)
    
    fieldsets = (
        ('Video', {
            'fields': ('video',)
        }),
        ('Resumen', {
            'fields': ('resumen_completo', 'temas_principales', 'conclusiones_clave', 'puntos_importantes')
        }),
        ('Metadata', {
            'fields': ('cantidad_palabras', 'modelo_ia_utilizado', 'fecha_generacion')
        }),
    )

class EtiquetaSegmentoInline(admin.TabularInline):
    model = EtiquetaSegmento
    extra = 1

@admin.register(Segmento)
class SegmentoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'video', 'timestamp_inicio_formateado', 'timestamp_fin_formateado', 'duracion_seg', 'orden', 'relevancia_score', 'tipo_contenido')
    list_filter = ('tipo_contenido', 'fecha_creacion')
    search_fields = ('titulo', 'descripcion', 'video__titulo')
    readonly_fields = ('fecha_creacion', 'timestamp_inicio_formateado', 'timestamp_fin_formateado')
    inlines = [EtiquetaSegmentoInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('video', 'titulo', 'descripcion', 'tipo_contenido')
        }),
        ('Timestamps', {
            'fields': ('timestamp_inicio_seg', 'timestamp_fin_seg', 'duracion_seg', 'timestamp_inicio_formateado', 'timestamp_fin_formateado')
        }),
        ('Relevancia', {
            'fields': ('orden', 'relevancia_score')
        }),
        ('Archivo', {
            'fields': ('ruta_archivo_segmento', 'miniatura_url')
        }),
        ('Metadata', {
            'fields': ('fecha_creacion',)
        }),
    )

@admin.register(EtiquetaVideo)
class EtiquetaVideoAdmin(admin.ModelAdmin):
    list_display = ('etiqueta', 'video', 'categoria', 'fecha_asignacion')
    list_filter = ('categoria', 'fecha_asignacion')
    search_fields = ('etiqueta', 'video__titulo')
    readonly_fields = ('fecha_asignacion',)

@admin.register(EtiquetaSegmento)
class EtiquetaSegmentoAdmin(admin.ModelAdmin):
    list_display = ('etiqueta', 'segmento', 'confianza', 'fecha_asignacion')
    list_filter = ('fecha_asignacion',)
    search_fields = ('etiqueta', 'segmento__titulo')
    readonly_fields = ('fecha_asignacion',)

@admin.register(LogProcesamiento)
class LogProcesamientoAdmin(admin.ModelAdmin):
    list_display = ('video', 'etapa', 'estado', 'timestamp', 'duracion_ms')
    list_filter = ('estado', 'etapa', 'timestamp')
    search_fields = ('video__titulo', 'mensaje', 'error_detalle')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Video y Etapa', {
            'fields': ('video', 'etapa', 'estado')
        }),
        ('Detalles', {
            'fields': ('mensaje', 'error_detalle', 'duracion_ms')
        }),
        ('Timestamp', {
            'fields': ('timestamp',)
        }),
    )

@admin.register(ConfiguracionSistema)
class ConfiguracionSistemaAdmin(admin.ModelAdmin):
    list_display = ('parametro', 'valor_truncado', 'modificado_por', 'fecha_modificacion')
    search_fields = ('parametro', 'descripcion', 'valor')
    readonly_fields = ('fecha_modificacion',)
    
    def valor_truncado(self, obj):
        return obj.valor[:50] + '...' if len(obj.valor) > 50 else obj.valor
    valor_truncado.short_description = 'Valor'
    
    fieldsets = (
        ('Configuración', {
            'fields': ('parametro', 'valor', 'descripcion')
        }),
        ('Metadata', {
            'fields': ('modificado_por', 'fecha_modificacion')
        }),
    )