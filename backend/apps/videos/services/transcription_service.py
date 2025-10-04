import whisper
import torch
from openai import OpenAI
from pathlib import Path
from typing import Optional, Dict, List
from django.conf import settings
from apps.videos.models import Video, Transcripcion, LogProcesamiento
import logging
import json

logger = logging.getLogger(__name__)


class TranscriptionError(Exception):
    """Excepción personalizada para errores de transcripción"""
    pass


class TranscriptionService:
    """
    Servicio para transcribir audio usando Whisper (Local o API)
    """
    
    def __init__(self, video: Video, mode: str = None):
        self.video = video
        self.mode = mode or settings.WHISPER_MODE
        self.model = None
        self.model_name = settings.WHISPER_MODEL
        self.device = settings.WHISPER_DEVICE
        
        # Cliente de OpenAI para API
        if self.mode == 'api':
            if not settings.OPENAI_API_KEY:
                raise TranscriptionError("OPENAI_API_KEY no configurada")
            self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    def load_model(self):
        """
        Cargar modelo de Whisper local
        Solo necesario si mode='local'
        """
        if self.mode != 'local':
            return
        
        try:
            if self.model is None:
                logger.info(f'Cargando modelo Whisper local: {self.model_name}')
                
                # Verificar si CUDA está disponible
                if self.device == 'cuda' and not torch.cuda.is_available():
                    logger.warning('CUDA no disponible, usando CPU')
                    self.device = 'cpu'
                
                # Cargar modelo
                self.model = whisper.load_model(
                    self.model_name,
                    device=self.device
                )
                
                logger.info(f'Modelo Whisper cargado en {self.device}')
        
        except Exception as e:
            error_msg = f"Error al cargar modelo Whisper: {str(e)}"
            logger.error(error_msg)
            raise TranscriptionError(error_msg)
    
    def transcribe(self, audio_path: Path) -> Dict:
        """
        Transcribir audio a texto (usando local o API según configuración)
        
        Args:
            audio_path: Ruta del archivo de audio
        
        Returns:
            Dict: Diccionario con transcripción y metadata
        """
        try:
            self._log_progress(
                'transcripcion',
                'iniciado',
                f'Iniciando transcripción de audio (modo: {self.mode})'
            )
            
            # Validar archivo
            if not audio_path.exists():
                raise TranscriptionError(f"Archivo de audio no existe: {audio_path}")
            
            # Validar tamaño (API tiene límite de 25MB)
            file_size_mb = audio_path.stat().st_size / (1024 * 1024)
            if self.mode == 'api' and file_size_mb > 25:
                raise TranscriptionError(
                    f"Archivo muy grande para API ({file_size_mb:.2f}MB). "
                    "Límite: 25MB. Usa modo 'local' o divide el audio."
                )
            
            logger.info(f'Transcribiendo audio ({self.mode}): {audio_path}')
            
            # Transcribir según modo
            if self.mode == 'api':
                result = self._transcribe_with_api(audio_path)
            else:
                result = self._transcribe_with_local(audio_path)
            
            # Procesar resultado
            transcription_data = self._process_transcription(result)
            
            # Guardar en base de datos
            self._save_transcription(transcription_data)
            
            self._log_progress(
                'transcripcion',
                'completado',
                f'Transcripción completada. Idioma: {transcription_data["idioma"]}'
            )
            
            logger.info(f'Transcripción completada para video {self.video.id}')
            
            return transcription_data
        
        except Exception as e:
            error_msg = f"Error al transcribir audio: {str(e)}"
            self._log_progress('transcripcion', 'error', error_msg, str(e))
            logger.error(error_msg)
            raise TranscriptionError(error_msg)
    
    def _transcribe_with_api(self, audio_path: Path) -> Dict:
        """
        Transcribir usando API de OpenAI
        
        Args:
            audio_path: Ruta del archivo de audio
        
        Returns:
            Dict: Resultado de la transcripción
        """
        try:
            logger.info('Usando API de OpenAI Whisper')
            
            # Abrir archivo de audio
            with open(audio_path, 'rb') as audio_file:
                # Llamar a la API
                response = self.openai_client.audio.transcriptions.create(
                    model=settings.WHISPER_API_MODEL,
                    file=audio_file,
                    response_format="verbose_json",  # Incluye timestamps
                    language=settings.WHISPER_LANGUAGE  # None para auto-detección
                )
            
            # Convertir respuesta a formato compatible
            result = {
                'text': response.text,
                'language': response.language,
                'duration': response.duration,
                'segments': []
            }
            
            # Procesar segmentos si están disponibles
            if hasattr(response, 'segments') and response.segments:
                for segment in response.segments:
                    result['segments'].append({
                        'start': segment.start,
                        'end': segment.end,
                        'text': segment.text,
                        'words': getattr(segment, 'words', [])
                    })
            
            return result
        
        except Exception as e:
            logger.error(f'Error en API de OpenAI: {str(e)}')
            raise TranscriptionError(f"Error en API de OpenAI: {str(e)}")
    
    def _transcribe_with_local(self, audio_path: Path) -> Dict:
        """
        Transcribir usando modelo local de Whisper
        
        Args:
            audio_path: Ruta del archivo de audio
        
        Returns:
            Dict: Resultado de la transcripción
        """
        try:
            logger.info('Usando modelo local de Whisper')
            
            # Cargar modelo si no está cargado
            if self.model is None:
                self.load_model()
            
            # Opciones de transcripción
            options = {
                'language': settings.WHISPER_LANGUAGE,
                'task': 'transcribe',
                'verbose': False,
                'word_timestamps': True,
            }
            
            # Transcribir
            result = self.model.transcribe(
                str(audio_path),
                **options
            )
            
            return result
        
        except Exception as e:
            logger.error(f'Error en transcripción local: {str(e)}')
            raise TranscriptionError(f"Error en transcripción local: {str(e)}")
    
    def _process_transcription(self, result: Dict) -> Dict:
        """
        Procesar resultado de Whisper y extraer información relevante
        """
        # Texto completo
        texto_completo = result['text'].strip()
        
        # Idioma detectado
        idioma = result.get('language', 'unknown')
        
        # Segmentos con timestamps
        segmentos = []
        for segment in result.get('segments', []):
            seg_data = {
                'inicio': segment.get('start', 0),
                'fin': segment.get('end', 0),
                'texto': segment.get('text', '').strip(),
                'palabras': []
            }
            
            # Extraer palabras si están disponibles
            if 'words' in segment:
                seg_data['palabras'] = self._extract_words(segment)
            
            segmentos.append(seg_data)
        
        # Calcular precisión estimada
        precision = self._calculate_precision(result)
        
        return {
            'contenido_completo': texto_completo,
            'idioma': idioma,
            'precision_estimada': precision,
            'segmentos': segmentos,
            'duracion': result.get('duration', 0),
        }
    
    def _extract_words(self, segment: Dict) -> List[Dict]:
        """Extraer palabras individuales con timestamps"""
        words = []
        for word in segment.get('words', []):
            words.append({
                'palabra': word.get('word', '').strip(),
                'inicio': word.get('start', 0),
                'fin': word.get('end', 0),
                'probabilidad': word.get('probability', 0)
            })
        return words
    
    def _calculate_precision(self, result: Dict) -> float:
        """Calcular precisión estimada de la transcripción"""
        segments = result.get('segments', [])
        if not segments:
            return 95.0  # Valor por defecto para API
        
        # Para API de OpenAI, usar valor alto por defecto
        if self.mode == 'api':
            return 95.0
        
        # Para local, calcular basado en log probabilities
        total_logprob = sum(seg.get('avg_logprob', 0) for seg in segments)
        avg_logprob = total_logprob / len(segments)
        precision = min(100, max(0, (1 + avg_logprob) * 100))
        
        return round(precision, 2)
    
    def _save_transcription(self, data: Dict):
        """Guardar transcripción en la base de datos"""
        try:
            modelo_usado = f"whisper-{self.mode}"
            if self.mode == 'local':
                modelo_usado = f"whisper-{self.model_name}"
            elif self.mode == 'api':
                modelo_usado = f"whisper-api-{settings.WHISPER_API_MODEL}"
            
            # Verificar si ya existe transcripción
            if hasattr(self.video, 'transcripcion'):
                transcripcion = self.video.transcripcion
                transcripcion.contenido_completo = data['contenido_completo']
                transcripcion.idioma_detectado = data['idioma']
                transcripcion.precision_estimada = data['precision_estimada']
                transcripcion.transcripcion_con_timestamps = data['segmentos']
                transcripcion.modelo_utilizado = modelo_usado
                transcripcion.save()
            else:
                Transcripcion.objects.create(
                    video=self.video,
                    contenido_completo=data['contenido_completo'],
                    idioma_detectado=data['idioma'],
                    precision_estimada=data['precision_estimada'],
                    transcripcion_con_timestamps=data['segmentos'],
                    modelo_utilizado=modelo_usado
                )
            
            logger.info(f'Transcripción guardada para video {self.video.id}')
        
        except Exception as e:
            logger.error(f'Error al guardar transcripción: {str(e)}')
            raise
    
    def detect_language(self, audio_path: Path) -> str:
        """
        Detectar idioma del audio
        Solo disponible en modo local
        """
        if self.mode == 'api':
            logger.warning('Detección de idioma no disponible en modo API')
            return 'unknown'
        
        try:
            if self.model is None:
                self.load_model()
            
            # Cargar primeros 30 segundos
            audio = whisper.load_audio(str(audio_path))
            audio = whisper.pad_or_trim(audio)
            
            # Hacer mel spectrogram
            mel = whisper.log_mel_spectrogram(audio).to(self.model.device)
            
            # Detectar idioma
            _, probs = self.model.detect_language(mel)
            detected_language = max(probs, key=probs.get)
            
            logger.info(
                f'Idioma detectado: {detected_language} '
                f'(confianza: {probs[detected_language]:.2%})'
            )
            
            return detected_language
        
        except Exception as e:
            logger.error(f'Error al detectar idioma: {str(e)}')
            return 'unknown'
    
    def get_transcription_text(self) -> Optional[str]:
        """Obtener texto de transcripción existente"""
        try:
            if hasattr(self.video, 'transcripcion'):
                return self.video.transcripcion.contenido_completo
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


def transcribe_audio(video_id: int, audio_path: Path, mode: str = None) -> Dict:
    """
    Función helper para transcribir audio de un video
    
    Args:
        video_id: ID del video
        audio_path: Ruta del archivo de audio
        mode: 'local' o 'api' (None usa settings)
    
    Returns:
        Dict: Datos de la transcripción
    """
    try:
        video = Video.objects.get(id=video_id)
        service = TranscriptionService(video, mode=mode)
        return service.transcribe(audio_path)
    except Video.DoesNotExist:
        raise TranscriptionError(f"Video con ID {video_id} no existe")