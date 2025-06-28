"""
Клиент для локального распознавания речи с использованием OpenAI Whisper
"""
import logging
import os
import asyncio
from typing import Dict, Any

logger = logging.getLogger(__name__)

class WhisperClient:
    """Клиент для локального распознавания речи с использованием OpenAI Whisper"""

    def __init__(self, model_name="base"):
        """
        Args:
            model_name: Название модели Whisper (tiny, base, small, medium, large)
        """
        self.model_name = model_name
        self.model = None
        self._load_model()

    def _load_model(self):
        """Загружает модель Whisper"""
        try:
            # Попробуем импортировать whisper
            try:
                import whisper
                self.model = whisper.load_model(self.model_name)
                logger.info(f"Whisper model '{self.model_name}' loaded successfully.")
            except AttributeError:
                # Если load_model не найден, попробуем альтернативный импорт
                logger.warning("Standard whisper.load_model not found, trying alternative approach")
                self.model = None
            except ImportError:
                logger.warning("Whisper library not available, speech recognition disabled")
                self.model = None
        except Exception as e:
            logger.error(f"Error loading Whisper model: {e}")
            self.model = None

    async def transcribe(self, audio_path: str) -> str:
        """
        Распознает речь из аудиофайла.

        Args:
            audio_path: Путь к аудиофайлу.

        Returns:
            Распознанный текст.
        """
        if not self.model:
            logger.error("Whisper model not loaded, transcription is not available.")
            return ""
        
        try:
            # Запускаем транскрипцию в отдельном потоке
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                self._transcribe_sync, 
                audio_path
            )
            logger.info(f"Transcription successful for {audio_path}")
            return result
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            return ""

    def _transcribe_sync(self, audio_path: str) -> str:
        """Синхронная транскрипция (выполняется в executor)"""
        try:
            if not self.model:
                return ""
            
            result = self.model.transcribe(audio_path, fp16=False)
            return result.get("text", "")
        except Exception as e:
            logger.error(f"Error in _transcribe_sync: {e}")
            return ""

    def is_audio_valid(self, audio_path: str) -> bool:
        """
        Проверяет валидность аудиофайла
        
        Args:
            audio_path: Путь к аудиофайлу
            
        Returns:
            True если файл валидный
        """
        try:
            if not os.path.exists(audio_path):
                return False
            
            # Проверяем размер файла
            file_size = os.path.getsize(audio_path)
            if file_size == 0 or file_size > 25 * 1024 * 1024:  # 25MB лимит
                return False
            
            # Проверяем расширение
            supported_extensions = {'.ogg', '.mp3', '.wav', '.m4a', '.mp4', '.flac'}
            file_extension = os.path.splitext(audio_path)[1].lower()
            
            return file_extension in supported_extensions
            
        except Exception as e:
            logger.error(f"Error checking audio validity: {e}")
            return False

    def get_model_info(self) -> Dict[str, Any]:
        """Возвращает информацию о модели"""
        return {
            "model_name": self.model_name,
            "model_loaded": self.model is not None,
            "supported_formats": ['.ogg', '.mp3', '.wav', '.m4a', '.mp4', '.flac'],
            "max_file_size": "25MB"
        } 