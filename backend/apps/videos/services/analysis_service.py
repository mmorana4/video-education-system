from openai import OpenAI
from typing import Dict, List, Optional
from django.conf import settings
from apps.videos.models import Video, ResumenEjecutivo, Transcripcion, LogProcesamiento
import logging
import json
import re

logger = logging.getLogger(__name__)


class AnalysisError(Exception):
    """Excepción personalizada para errores de análisis"""
    pass


class AnalysisService:
    """
    Servicio para analizar transcripciones con GPT de OpenAI
    """
    
    def __init__(self, video: Video):
        self.video = video
        
        # Validar API key
        if not settings.OPENAI_API_KEY:
            raise AnalysisError("OPENAI_API_KEY no configurada")
        
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.GPT_MODEL
    
    def analyze(self) -> Dict:
        """
        Analizar transcripción del video y generar resumen ejecutivo
        
        Returns:
            Dict: Análisis completo del video
        
        Raises:
            AnalysisError: Si hay error en el análisis
        """
        try:
            self._log_progress('analisis_ia', 'iniciado', 'Iniciando análisis con IA')
            
            # Obtener transcripción
            transcripcion = self._get_transcription()
            if not transcripcion:
                raise AnalysisError("El video no tiene transcripción")
            
            logger.info(f'Analizando video {self.video.id} con {self.model}')
            
            # Generar resumen ejecutivo
            resumen_data = self._generate_executive_summary(transcripcion)
            
            # Identificar segmentos importantes
            segmentos_importantes = self._identify_important_segments(transcripcion)
            
            # Combinar resultados
            analysis_result = {
                'resumen': resumen_data,
                'segmentos_importantes': segmentos_importantes
            }
            
            # Guardar en base de datos
            self._save_analysis(resumen_data)
            
            self._log_progress(
                'analisis_ia',
                'completado',
                f'Análisis completado. {len(segmentos_importantes)} segmentos identificados'
            )
            
            logger.info(f'Análisis completado para video {self.video.id}')
            
            return analysis_result
        
        except Exception as e:
            error_msg = f"Error al analizar video: {str(e)}"
            self._log_progress('analisis_ia', 'error', error_msg, str(e))
            logger.error(error_msg)
            raise AnalysisError(error_msg)
    
    def _get_transcription(self) -> Optional[str]:
        """Obtener transcripción del video"""
        try:
            if hasattr(self.video, 'transcripcion'):
                return self.video.transcripcion.contenido_completo
            return None
        except Transcripcion.DoesNotExist:
            return None
    
    def _generate_executive_summary(self, transcription: str) -> Dict:
        """
        Generar resumen ejecutivo usando GPT
        
        Args:
            transcription: Texto de la transcripción
        
        Returns:
            Dict: Resumen ejecutivo estructurado
        """
        try:
            logger.info('Generando resumen ejecutivo...')
            
            # Prompt para resumen ejecutivo
            system_prompt = """Eres un asistente experto en análisis de contenido educativo universitario. 
Tu tarea es analizar transcripciones de clases y generar resúmenes ejecutivos claros y concisos.

Debes responder SIEMPRE en formato JSON con esta estructura exacta:
{
    "resumen_completo": "Resumen general del contenido (2-3 párrafos)",
    "temas_principales": ["Tema 1", "Tema 2", "Tema 3", ...],
    "conclusiones_clave": ["Conclusión 1", "Conclusión 2", ...],
    "puntos_importantes": ["Punto 1", "Punto 2", "Punto 3", ...]
}

Enfócate en:
- Conceptos clave enseñados
- Relaciones entre conceptos
- Aplicaciones prácticas mencionadas
- Conclusiones del docente"""

            user_prompt = f"""Analiza la siguiente transcripción de una clase universitaria y genera un resumen ejecutivo:

TRANSCRIPCIÓN:
{transcription[:8000]}

Genera el resumen en formato JSON."""

            # Llamar a GPT
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=settings.GPT_TEMPERATURE,
                max_tokens=settings.GPT_MAX_TOKENS,
                response_format={"type": "json_object"}
            )
            
            # Parsear respuesta
            result = json.loads(response.choices[0].message.content)
            
            logger.info('Resumen ejecutivo generado')
            
            return result
        
        except Exception as e:
            logger.error(f'Error al generar resumen: {str(e)}')
            raise AnalysisError(f"Error al generar resumen: {str(e)}")
    
    def _identify_important_segments(self, transcription: str) -> List[Dict]:
        """
        Identificar segmentos importantes con timestamps
        
        Args:
            transcription: Texto de la transcripción
        
        Returns:
            List[Dict]: Lista de segmentos importantes
        """
        try:
            logger.info('Identificando segmentos importantes...')
            
            # Obtener transcripción con timestamps
            transcripcion_obj = self.video.transcripcion
            segmentos_con_timestamps = transcripcion_obj.transcripcion_con_timestamps
            
            if not segmentos_con_timestamps:
                logger.warning('No hay segmentos con timestamps')
                return []
            
            # Crear texto con referencias de tiempo para GPT
            texto_con_tiempos = self._format_transcription_with_times(segmentos_con_timestamps)
            
            # Prompt para identificar segmentos
            system_prompt = """Eres un experto en identificar los momentos más importantes de clases universitarias.

Tu tarea es identificar los segmentos MÁS RELEVANTES para el aprendizaje.

Debes responder en formato JSON con esta estructura:
{
    "segmentos": [
        {
            "titulo": "Título descriptivo del segmento",
            "descripcion": "Breve descripción del contenido (1-2 oraciones)",
            "timestamp_inicio": segundos_de_inicio,
            "timestamp_fin": segundos_de_fin,
            "relevancia": puntuación_de_1_a_10,
            "tipo": "introduccion|concepto_clave|ejemplo|demostracion|conclusion|ejercicio"
        }
    ]
}

Busca:
- Introducciones a nuevos conceptos
- Explicaciones de conceptos clave
- Ejemplos importantes
- Demostraciones prácticas
- Conclusiones relevantes
- Ejercicios o problemas resueltos

Identifica entre 3 y 10 segmentos, priorizando calidad sobre cantidad."""

            min_segs = settings.ANALYSIS_MIN_SEGMENTS
            max_segs = settings.ANALYSIS_MAX_SEGMENTS
            
            user_prompt = f"""Analiza esta transcripción con timestamps e identifica los {min_segs}-{max_segs} segmentos MÁS IMPORTANTES:

{texto_con_tiempos[:10000]}

Responde en formato JSON."""

            # Llamar a GPT
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=settings.GPT_TEMPERATURE,
                max_tokens=settings.GPT_MAX_TOKENS,
                response_format={"type": "json_object"}
            )
            
            # Parsear respuesta
            result = json.loads(response.choices[0].message.content)
            segmentos = result.get('segmentos', [])
            
            # Validar y limpiar segmentos
            segmentos_validados = self._validate_segments(segmentos)
            
            logger.info(f'{len(segmentos_validados)} segmentos importantes identificados')
            
            return segmentos_validados
        
        except Exception as e:
            logger.error(f'Error al identificar segmentos: {str(e)}')
            return []
    
    def _format_transcription_with_times(self, segments: List[Dict]) -> str:
        """
        Formatear transcripción con timestamps para GPT
        
        Args:
            segments: Lista de segmentos con timestamps
        
        Returns:
            str: Texto formateado
        """
        formatted_lines = []
        
        for seg in segments:
            inicio = seg.get('inicio', 0)
            texto = seg.get('texto', '').strip()
            
            # Formatear tiempo en MM:SS
            minutos = int(inicio // 60)
            segundos = int(inicio % 60)
            tiempo_fmt = f"[{minutos:02d}:{segundos:02d}]"
            
            formatted_lines.append(f"{tiempo_fmt} {texto}")
        
        return "\n".join(formatted_lines)
    
    def _validate_segments(self, segments: List[Dict]) -> List[Dict]:
        """
        Validar y limpiar segmentos identificados
        
        Args:
            segments: Lista de segmentos sin validar
        
        Returns:
            List[Dict]: Segmentos validados
        """
        validados = []
        
        for seg in segments:
            try:
                # Validar campos requeridos
                if not all(k in seg for k in ['titulo', 'timestamp_inicio', 'timestamp_fin']):
                    continue
                
                # Validar timestamps
                inicio = int(seg['timestamp_inicio'])
                fin = int(seg['timestamp_fin'])
                
                if inicio < 0 or fin <= inicio:
                    continue
                
                if self.video.duracion_segundos and fin > self.video.duracion_segundos:
                    fin = self.video.duracion_segundos
                
                # Calcular duración
                duracion = fin - inicio
                
                # Validar tipo
                tipos_validos = [
                    'introduccion', 'concepto_clave', 'ejemplo',
                    'demostracion', 'conclusion', 'ejercicio', 'otro'
                ]
                tipo = seg.get('tipo', 'otro')
                if tipo not in tipos_validos:
                    tipo = 'otro'
                
                # Validar relevancia
                relevancia = float(seg.get('relevancia', 7.0))
                relevancia = max(1.0, min(10.0, relevancia))
                
                validados.append({
                    'titulo': seg['titulo'][:255],
                    'descripcion': seg.get('descripcion', '')[:500],
                    'timestamp_inicio': inicio,
                    'timestamp_fin': fin,
                    'duracion': duracion,
                    'relevancia': relevancia,
                    'tipo': tipo
                })
            
            except (ValueError, TypeError) as e:
                logger.warning(f'Segmento inválido ignorado: {e}')
                continue
        
        # Ordenar por relevancia descendente
        validados.sort(key=lambda x: x['relevancia'], reverse=True)
        
        # Limitar cantidad
        max_segments = settings.ANALYSIS_MAX_SEGMENTS
        return validados[:max_segments]
    
    def _save_analysis(self, resumen_data: Dict):
        """
        Guardar resumen ejecutivo en la base de datos
        
        Args:
            resumen_data: Datos del resumen
        """
        try:
            # Convertir listas a texto
            temas = "\n".join([f"• {tema}" for tema in resumen_data.get('temas_principales', [])])
            conclusiones = "\n".join([f"• {c}" for c in resumen_data.get('conclusiones_clave', [])])
            puntos = "\n".join([f"• {p}" for p in resumen_data.get('puntos_importantes', [])])
            
            resumen_completo = resumen_data.get('resumen_completo', '')
            cantidad_palabras = len(resumen_completo.split())
            
            # Verificar si ya existe resumen
            if hasattr(self.video, 'resumen_ejecutivo'):
                resumen = self.video.resumen_ejecutivo
                resumen.resumen_completo = resumen_completo
                resumen.temas_principales = temas
                resumen.conclusiones_clave = conclusiones
                resumen.puntos_importantes = puntos
                resumen.cantidad_palabras = cantidad_palabras
                resumen.modelo_ia_utilizado = self.model
                resumen.save()
            else:
                ResumenEjecutivo.objects.create(
                    video=self.video,
                    resumen_completo=resumen_completo,
                    temas_principales=temas,
                    conclusiones_clave=conclusiones,
                    puntos_importantes=puntos,
                    cantidad_palabras=cantidad_palabras,
                    modelo_ia_utilizado=self.model
                )
            
            logger.info(f'Resumen guardado para video {self.video.id}')
        
        except Exception as e:
            logger.error(f'Error al guardar resumen: {str(e)}')
            raise
    
    def get_existing_summary(self) -> Optional[Dict]:
        """
        Obtener resumen ejecutivo existente
        
        Returns:
            Optional[Dict]: Resumen existente o None
        """
        try:
            if hasattr(self.video, 'resumen_ejecutivo'):
                resumen = self.video.resumen_ejecutivo
                return {
                    'resumen_completo': resumen.resumen_completo,
                    'temas_principales': resumen.temas_principales.split('\n'),
                    'conclusiones_clave': resumen.conclusiones_clave.split('\n'),
                    'puntos_importantes': resumen.puntos_importantes.split('\n'),
                    'modelo_utilizado': resumen.modelo_ia_utilizado
                }
            return None
        except Exception:
            return None
    
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


def analyze_video(video_id: int) -> Dict:
    """
    Función helper para analizar un video
    
    Args:
        video_id: ID del video
    
    Returns:
        Dict: Resultado del análisis
    """
    try:
        video = Video.objects.get(id=video_id)
        service = AnalysisService(video)
        return service.analyze()
    except Video.DoesNotExist:
        raise AnalysisError(f"Video con ID {video_id} no existe")