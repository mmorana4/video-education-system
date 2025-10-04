from rest_framework import serializers
from apps.videos.models import (
    Video, Segmento, Transcripcion, ResumenEjecutivo,
    EtiquetaVideo, EtiquetaSegmento
)
from django.contrib.auth import get_user_model

Usuario = get_user_model()


class UsuarioSimpleSerializer(serializers.ModelSerializer):
    """Serializer simple para mostrar info básica del usuario"""
    class Meta:
        model = Usuario
        fields = ('id', 'username', 'nombre_completo', 'email')
        read_only_fields = fields


class EtiquetaVideoSerializer(serializers.ModelSerializer):
    """Serializer para etiquetas de video"""
    class Meta:
        model = EtiquetaVideo
        fields = ('id', 'etiqueta', 'categoria', 'fecha_asignacion')
        read_only_fields = ('id', 'fecha_asignacion')


class VideoListSerializer(serializers.ModelSerializer):
    """Serializer para listar videos (vista resumida)"""
    usuario = UsuarioSimpleSerializer(read_only=True)
    duracion_formateada = serializers.CharField(read_only=True)
    cantidad_segmentos = serializers.SerializerMethodField()
    tiene_transcripcion = serializers.SerializerMethodField()
    tiene_resumen = serializers.SerializerMethodField()
    
    class Meta:
        model = Video
        fields = (
            'id', 'titulo', 'usuario', 'fuente', 'estado',
            'duracion_segundos', 'duracion_formateada', 'fecha_subida',
            'miniatura_url', 'cantidad_segmentos', 'tiene_transcripcion',
            'tiene_resumen'
        )
        read_only_fields = fields
    
    def get_cantidad_segmentos(self, obj):
        """Retorna la cantidad de segmentos del video"""
        return obj.segmentos.count()
    
    def get_tiene_transcripcion(self, obj):
        """Verifica si el video tiene transcripción"""
        return hasattr(obj, 'transcripcion')
    
    def get_tiene_resumen(self, obj):
        """Verifica si el video tiene resumen ejecutivo"""
        return hasattr(obj, 'resumen_ejecutivo')


class VideoCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear videos"""
    class Meta:
        model = Video
        fields = (
            'titulo', 'url_original', 'fuente', 'ruta_video_completo'
        )
    
    def validate_fuente(self, value):
        """Validar que la fuente sea válida"""
        fuentes_validas = [choice[0] for choice in Video.FUENTE_CHOICES]
        if value not in fuentes_validas:
            raise serializers.ValidationError(
                f"Fuente inválida. Opciones: {', '.join(fuentes_validas)}"
            )
        return value
    
    def validate(self, attrs):
        """Validar que se proporcione URL o archivo"""
        url_original = attrs.get('url_original')
        ruta_video_completo = attrs.get('ruta_video_completo')
        
        if not url_original and not ruta_video_completo:
            raise serializers.ValidationError(
                "Debe proporcionar una URL o subir un archivo de video."
            )
        
        return attrs
    
    def create(self, validated_data):
        """Crear video asignando el usuario autenticado"""
        validated_data['usuario'] = self.context['request'].user
        validated_data['estado'] = 'pendiente'
        return super().create(validated_data)


class VideoDetailSerializer(serializers.ModelSerializer):
    """Serializer para detalle completo del video"""
    usuario = UsuarioSimpleSerializer(read_only=True)
    duracion_formateada = serializers.CharField(read_only=True)
    etiquetas = EtiquetaVideoSerializer(many=True, read_only=True)
    
    class Meta:
        model = Video
        fields = (
            'id', 'titulo', 'usuario', 'url_original', 'fuente',
            'ruta_video_completo', 'duracion_segundos', 'duracion_formateada',
            'formato', 'tamano_mb', 'estado', 'fecha_subida',
            'fecha_procesamiento', 'miniatura_url', 'metadata_json',
            'etiquetas'
        )
        read_only_fields = (
            'id', 'usuario', 'duracion_segundos', 'formato', 'tamano_mb',
            'fecha_subida', 'fecha_procesamiento', 'duracion_formateada'
        )


class VideoUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar videos"""
    class Meta:
        model = Video
        fields = ('titulo', 'estado')
    
    def validate_estado(self, value):
        """Validar que el estado sea válido"""
        estados_validos = [choice[0] for choice in Video.ESTADO_CHOICES]
        if value not in estados_validos:
            raise serializers.ValidationError(
                f"Estado inválido. Opciones: {', '.join(estados_validos)}"
            )
        return value
    
class EtiquetaSegmentoSerializer(serializers.ModelSerializer):
    """Serializer para etiquetas de segmento"""
    class Meta:
        model = EtiquetaSegmento
        fields = ('id', 'etiqueta', 'confianza', 'fecha_asignacion')
        read_only_fields = ('id', 'fecha_asignacion')


class SegmentoListSerializer(serializers.ModelSerializer):
    """Serializer para listar segmentos"""
    timestamp_inicio_formateado = serializers.CharField(read_only=True)
    timestamp_fin_formateado = serializers.CharField(read_only=True)
    video_titulo = serializers.CharField(source='video.titulo', read_only=True)
    
    class Meta:
        model = Segmento
        fields = (
            'id', 'video', 'video_titulo', 'titulo', 'descripcion',
            'timestamp_inicio_seg', 'timestamp_fin_seg',
            'timestamp_inicio_formateado', 'timestamp_fin_formateado',
            'duracion_seg', 'orden', 'relevancia_score', 'tipo_contenido',
            'miniatura_url'
        )
        read_only_fields = (
            'id', 'duracion_seg', 'timestamp_inicio_formateado',
            'timestamp_fin_formateado'
        )


class SegmentoDetailSerializer(serializers.ModelSerializer):
    """Serializer para detalle completo del segmento"""
    timestamp_inicio_formateado = serializers.CharField(read_only=True)
    timestamp_fin_formateado = serializers.CharField(read_only=True)
    etiquetas = EtiquetaSegmentoSerializer(many=True, read_only=True)
    video_titulo = serializers.CharField(source='video.titulo', read_only=True)
    
    class Meta:
        model = Segmento
        fields = (
            'id', 'video', 'video_titulo', 'titulo', 'descripcion',
            'timestamp_inicio_seg', 'timestamp_fin_seg',
            'timestamp_inicio_formateado', 'timestamp_fin_formateado',
            'duracion_seg', 'ruta_archivo_segmento', 'orden',
            'relevancia_score', 'tipo_contenido', 'fecha_creacion',
            'miniatura_url', 'etiquetas'
        )
        read_only_fields = (
            'id', 'duracion_seg', 'timestamp_inicio_formateado',
            'timestamp_fin_formateado', 'fecha_creacion'
        )
    
    def validate(self, attrs):
        """Validar que el timestamp de fin sea mayor al de inicio"""
        inicio = attrs.get('timestamp_inicio_seg')
        fin = attrs.get('timestamp_fin_seg')
        
        if inicio is not None and fin is not None:
            if fin <= inicio:
                raise serializers.ValidationError({
                    'timestamp_fin_seg': 'El timestamp de fin debe ser mayor al de inicio.'
                })
            
            # Calcular duración automáticamente
            attrs['duracion_seg'] = fin - inicio
        
        return attrs


class SegmentoCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear segmentos"""
    class Meta:
        model = Segmento
        fields = (
            'video', 'titulo', 'descripcion', 'timestamp_inicio_seg',
            'timestamp_fin_seg', 'orden', 'relevancia_score',
            'tipo_contenido'
        )
    
    def validate(self, attrs):
        """Validaciones de segmento"""
        inicio = attrs['timestamp_inicio_seg']
        fin = attrs['timestamp_fin_seg']
        video = attrs['video']
        
        # Validar que fin > inicio
        if fin <= inicio:
            raise serializers.ValidationError({
                'timestamp_fin_seg': 'El timestamp de fin debe ser mayor al de inicio.'
            })
        
        # Validar que los timestamps estén dentro de la duración del video
        if video.duracion_segundos:
            if inicio < 0 or fin > video.duracion_segundos:
                raise serializers.ValidationError(
                    f'Los timestamps deben estar entre 0 y {video.duracion_segundos} segundos.'
                )
        
        # Calcular duración
        attrs['duracion_seg'] = fin - inicio
        
        return attrs

class TranscripcionSerializer(serializers.ModelSerializer):
    """Serializer para transcripciones"""
    video_titulo = serializers.CharField(source='video.titulo', read_only=True)
    
    class Meta:
        model = Transcripcion
        fields = (
            'id', 'video', 'video_titulo', 'contenido_completo',
            'idioma_detectado', 'precision_estimada',
            'transcripcion_con_timestamps', 'fecha_generacion',
            'modelo_utilizado'
        )
        read_only_fields = ('id', 'fecha_generacion')


class ResumenEjecutivoSerializer(serializers.ModelSerializer):
    """Serializer para resúmenes ejecutivos"""
    video_titulo = serializers.CharField(source='video.titulo', read_only=True)
    
    class Meta:
        model = ResumenEjecutivo
        fields = (
            'id', 'video', 'video_titulo', 'resumen_completo',
            'temas_principales', 'conclusiones_clave', 'puntos_importantes',
            'cantidad_palabras', 'fecha_generacion', 'modelo_ia_utilizado'
        )
        read_only_fields = ('id', 'fecha_generacion', 'cantidad_palabras')
    
    def validate_resumen_completo(self, value):
        """Validar longitud mínima del resumen"""
        if len(value.split()) < 10:
            raise serializers.ValidationError(
                'El resumen debe tener al menos 10 palabras.'
            )
        return value
    
    def create(self, validated_data):
        """Calcular cantidad de palabras al crear"""
        resumen = validated_data.get('resumen_completo', '')
        validated_data['cantidad_palabras'] = len(resumen.split())
        return super().create(validated_data)
    
class VideoCompleteSerializer(serializers.ModelSerializer):
    """Serializer completo con todas las relaciones"""
    usuario = UsuarioSimpleSerializer(read_only=True)
    duracion_formateada = serializers.CharField(read_only=True)
    etiquetas = EtiquetaVideoSerializer(many=True, read_only=True)
    segmentos = SegmentoListSerializer(many=True, read_only=True)
    transcripcion = TranscripcionSerializer(read_only=True)
    resumen_ejecutivo = ResumenEjecutivoSerializer(read_only=True)
    
    class Meta:
        model = Video
        fields = (
            'id', 'titulo', 'usuario', 'url_original', 'fuente',
            'ruta_video_completo', 'duracion_segundos', 'duracion_formateada',
            'formato', 'tamano_mb', 'estado', 'fecha_subida',
            'fecha_procesamiento', 'miniatura_url', 'metadata_json',
            'etiquetas', 'segmentos', 'transcripcion', 'resumen_ejecutivo'
        )
        read_only_fields = fields