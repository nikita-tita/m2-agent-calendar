"""
Упрощённый AI сервис
Только распознавание речи и текста
"""
import logging
from typing import Dict, Any

from app.ai.speech.whisper_client import WhisperClient
from app.ai.vision.ocr_client import OCRClient
from app.ai.nlp.gpt_client import GPTClient
from app.config import settings

logger = logging.getLogger(__name__)

class AIService:
    """Упрощённый AI сервис"""
    
    def __init__(self):
        # Инициализируем только нужные компоненты
        try:
            self.whisper_client = WhisperClient()
            logger.info("Whisper client initialized")
        except Exception as e:
            logger.warning(f"Whisper client not available: {e}")
            self.whisper_client = None
            
        try:
            self.ocr_client = OCRClient()
            logger.info("OCR client initialized")
        except Exception as e:
            logger.warning(f"OCR client not available: {e}")
            self.ocr_client = None
            
        try:
            if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "your-openai-api-key-here":
                self.gpt_client = GPTClient(settings.OPENAI_API_KEY)
                logger.info("GPT client initialized")
            else:
                self.gpt_client = None
                logger.warning("GPT client not available - no API key")
        except Exception as e:
            logger.warning(f"GPT client not available: {e}")
            self.gpt_client = None

    async def process_voice(self, file_path: str) -> Dict[str, Any]:
        """Обработка голосового сообщения"""
        try:
            # Распознавание речи
            if not self.whisper_client:
                return {"error": "Whisper client not available"}
                
            transcribed_text = await self.whisper_client.transcribe_audio(file_path)
            
            if not transcribed_text:
                return {"error": "Не удалось распознать речь"}
            
            return {
                "transcribed_text": transcribed_text
            }
            
        except Exception as e:
            logger.error(f"Voice processing error: {e}")
            return {"error": str(e)}

    async def process_image(self, file_path: str) -> Dict[str, Any]:
        """Обработка изображения"""
        try:
            # OCR обработка
            if not self.ocr_client:
                return {"error": "OCR client not available"}
                
            ocr_result = await self.ocr_client.extract_text_from_image(file_path)
            extracted_text = ocr_result.get("text", "") if isinstance(ocr_result, dict) else str(ocr_result)
            
            if not extracted_text:
                return {"error": "Не удалось извлечь текст из изображения"}
            
            return {
                "extracted_text": extracted_text,
                "ocr_result": ocr_result
            }
            
        except Exception as e:
            logger.error(f"Image processing error: {e}")
            return {"error": str(e)} 