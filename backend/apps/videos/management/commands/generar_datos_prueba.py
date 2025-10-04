from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.videos.models import (
    Video, Transcripcion, ResumenEjecutivo, Segmento,
    EtiquetaVideo, LogProcesamiento, ConfiguracionSistema
)
from datetime import datetime, timedelta
import random

Usuario = get_user_model()

class Command(BaseCommand):
    help = 'Genera datos de prueba para el sistema'

    def handle(self, *args, **kwargs):
        self.stdout.write('Generando datos de prueba...')
        
        # Crear usuarios de prueba
        usuarios = self.crear_usuarios()
        
        # Crear videos de prueba
        videos = self.crear_videos(usuarios)
        
        # Crear transcripciones
        self.crear_transcripciones(videos)
        
        # Crear resúmenes ejecutivos
        self.crear_resumenes(videos)
        
        # Crear segmentos
        self.crear_segmentos(videos)
        
        # Crear configuraciones
        self.crear_configuraciones(usuarios)
        
        self.stdout.write(self.style.SUCCESS('¡Datos de prueba generados exitosamente!'))
    
    def crear_usuarios(self):
        self.stdout.write('Creando usuarios...')
        usuarios = []
        
        # Verificar si ya existen
        if Usuario.objects.filter(username='docente1').exists():
            self.stdout.write(self.style.WARNING('Los usuarios ya existen, omitiendo...'))
            return Usuario.objects.filter(rol='docente')[:3]
        
        usuarios_data = [
            {
                'username': 'docente1',
                'email': 'docente1@universidad.edu',
                'first_name': 'María',
                'last_name': 'González',
                'rol': 'docente'
            },
            {
                'username': 'docente2',
                'email': 'docente2@universidad.edu',
                'first_name': 'Carlos',
                'last_name': 'Ramírez',
                'rol': 'docente'
            },
            {
                'username': 'admin1',
                'email': 'admin1@universidad.edu',
                'first_name': 'Ana',
                'last_name': 'Martínez',
                'rol': 'admin'
            }
        ]
        
        for data in usuarios_data:
            usuario = Usuario.objects.create_user(
                username=data['username'],
                email=data['email'],
                password='password123',
                first_name=data['first_name'],
                last_name=data['last_name'],
                rol=data['rol']
            )
            usuarios.append(usuario)
            self.stdout.write(f'  ✓ Usuario creado: {usuario.username}')
        
        return usuarios
    
    def crear_videos(self, usuarios):
        self.stdout.write('Creando videos...')
        videos = []
        
        videos_data = [
            {
                'titulo': 'Introducción a Python - Clase 1',
                'url_original': 'https://www.youtube.com/watch?v=example1',
                'fuente': 'youtube',
                'duracion_segundos': 3600,
                'estado': 'completado'
            },
            {
                'titulo': 'Programación Orientada a Objetos',
                'url_original': 'https://www.youtube.com/watch?v=example2',
                'fuente': 'youtube',
                'duracion_segundos': 2700,
                'estado': 'completado'
            },
            {
                'titulo': 'Bases de Datos Relacionales',
                'url_original': 'https://www.youtube.com/watch?v=example3',
                'fuente': 'youtube',
                'duracion_segundos': 4200,
                'estado': 'procesando'
            },
            {
                'titulo': 'Desarrollo Web con Django',
                'url_original': 'https://www.youtube.com/watch?v=example4',
                'fuente': 'youtube',
                'duracion_segundos': 5400,
                'estado': 'completado'
            },
            {
                'titulo': 'React - Fundamentos',
                'url_original': 'https://www.youtube.com/watch?v=example5',
                'fuente': 'youtube',
                'duracion_segundos': 3000,
                'estado': 'pendiente'
            }
        ]
        
        for i, data in enumerate(videos_data):
            video = Video.objects.create(
                usuario=random.choice(usuarios),
                titulo=data['titulo'],
                url_original=data['url_original'],
                fuente=data['fuente'],
                duracion_segundos=data['duracion_segundos'],
                formato='mp4',
                tamano_mb=round(random.uniform(100, 500), 2),
                estado=data['estado'],
                fecha_subida=datetime.now() - timedelta(days=random.randint(1, 30)),
                fecha_procesamiento=datetime.now() - timedelta(days=random.randint(0, 15)) if data['estado'] == 'completado' else None,
                metadata_json={
                    'resolucion': '1920x1080',
                    'fps': 30,
                    'codec': 'h264'
                }
            )
            videos.append(video)
            self.stdout.write(f'  ✓ Video creado: {video.titulo}')
            
            # Crear etiquetas para el video
            etiquetas = ['programación', 'tutorial', 'universidad', 'educación']
            for etiqueta in random.sample(etiquetas, 2):
                EtiquetaVideo.objects.create(
                    video=video,
                    etiqueta=etiqueta,
                    categoria='general'
                )
            
            # Crear logs de procesamiento
            if video.estado != 'pendiente':
                etapas = ['descarga', 'extraccion_audio', 'transcripcion']
                for etapa in etapas:
                    LogProcesamiento.objects.create(
                        video=video,
                        etapa=etapa,
                        estado='completado',
                        mensaje=f'Etapa {etapa} completada exitosamente',
                        duracion_ms=random.randint(1000, 10000)
                    )
        
        return videos
    
    def crear_transcripciones(self, videos):
        self.stdout.write('Creando transcripciones...')
        
        for video in videos:
            if video.estado == 'completado':
                transcripcion = Transcripcion.objects.create(
                    video=video,
                    contenido_completo=f'Esta es la transcripción completa del video "{video.titulo}". '
                                     'En esta clase aprenderemos conceptos fundamentales sobre el tema. '
                                     'Comenzaremos con una introducción general, luego veremos ejemplos prácticos '
                                     'y finalmente realizaremos ejercicios de aplicación.',
                    idioma_detectado='es',
                    precision_estimada=95.5,
                    transcripcion_con_timestamps=[
                        {'inicio': 0, 'fin': 30, 'texto': 'Bienvenidos a esta clase...'},
                        {'inicio': 30, 'fin': 120, 'texto': 'Hoy veremos los conceptos principales...'},
                        {'inicio': 120, 'fin': 300, 'texto': 'Comenzaremos con un ejemplo...'}
                    ],
                    modelo_utilizado='whisper-large-v3'
                )
                self.stdout.write(f'  ✓ Transcripción creada para: {video.titulo}')
    
    def crear_resumenes(self, videos):
        self.stdout.write('Creando resúmenes ejecutivos...')
        
        for video in videos:
            if video.estado == 'completado':
                resumen = ResumenEjecutivo.objects.create(
                    video=video,
                    resumen_completo=f'Este video presenta una introducción completa a {video.titulo}. '
                                    'Se cubren los conceptos fundamentales necesarios para comprender el tema, '
                                    'se presentan ejemplos prácticos y se proponen ejercicios de aplicación.',
                    temas_principales='1. Introducción al tema\n2. Conceptos básicos\n3. Ejemplos prácticos\n4. Ejercicios',
                    conclusiones_clave='- El tema es fundamental para el desarrollo profesional\n'
                                      '- Es importante practicar con ejemplos reales\n'
                                      '- Los ejercicios ayudan a consolidar el conocimiento',
                    puntos_importantes='• Definiciones clave explicadas\n'
                                      '• Ejemplos del mundo real\n'
                                      '• Buenas prácticas recomendadas',
                    cantidad_palabras=random.randint(200, 500),
                    modelo_ia_utilizado='gpt-4'
                )
                self.stdout.write(f'  ✓ Resumen creado para: {video.titulo}')
    
    def crear_segmentos(self, videos):
        self.stdout.write('Creando segmentos...')
        
        for video in videos:
            if video.estado == 'completado':
                # Crear entre 3 y 5 segmentos por video
                num_segmentos = random.randint(3, 5)
                duracion_total = video.duracion_segundos
                segmento_duracion = duracion_total // num_segmentos
                
                tipos = ['introduccion', 'concepto_clave', 'ejemplo', 'demostracion', 'conclusion']
                
                for i in range(num_segmentos):
                    inicio = i * segmento_duracion
                    fin = inicio + segmento_duracion if i < num_segmentos - 1 else duracion_total
                    
                    segmento = Segmento.objects.create(
                        video=video,
                        titulo=f'Segmento {i+1}: {tipos[i % len(tipos)].replace("_", " ").title()}',
                        descripcion=f'Descripción del segmento importante número {i+1}. '
                                   'Este segmento contiene información relevante para el aprendizaje.',
                        timestamp_inicio_seg=inicio,
                        timestamp_fin_seg=fin,
                        duracion_seg=fin - inicio,
                        orden=i + 1,
                        relevancia_score=round(random.uniform(7.0, 10.0), 1),
                        tipo_contenido=tipos[i % len(tipos)]
                    )
                    self.stdout.write(f'  ✓ Segmento creado: {segmento.titulo}')
    
    def crear_configuraciones(self, usuarios):
        self.stdout.write('Creando configuraciones del sistema...')
        
        configuraciones = [
            {
                'parametro': 'max_video_size_mb',
                'valor': '500',
                'descripcion': 'Tamaño máximo permitido para videos en MB'
            },
            {
                'parametro': 'max_video_duration_seconds',
                'valor': '10800',
                'descripcion': 'Duración máxima permitida para videos en segundos (3 horas)'
            },
            {
                'parametro': 'transcription_model',
                'valor': 'whisper-large-v3',
                'descripcion': 'Modelo de transcripción a utilizar'
            },
            {
                'parametro': 'ai_summary_model',
                'valor': 'gpt-4',
                'descripcion': 'Modelo de IA para generar resúmenes'
            },
            {
                'parametro': 'min_segment_duration',
                'valor': '30',
                'descripcion': 'Duración mínima de un segmento en segundos'
            }
        ]
        
        for config in configuraciones:
            ConfiguracionSistema.objects.create(
                parametro=config['parametro'],
                valor=config['valor'],
                descripcion=config['descripcion'],
                modificado_por=random.choice(usuarios)
            )
            self.stdout.write(f'  ✓ Configuración creada: {config["parametro"]}')