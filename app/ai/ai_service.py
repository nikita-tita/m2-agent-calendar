import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from .speech.whisper_client import WhisperClient
from .nlp.gpt_client import GPTClient
from .vision.ocr_client import OCRClient

logger = logging.getLogger(__name__)


class AIService:
    """Упрощённый AI сервис"""
    
    def __init__(self):
        # Инициализируем компоненты
        try:
            self.gpt_client = GPTClient()
            logger.info("GPT client initialized")
        except Exception as e:
            logger.warning(f"GPT client not available: {e}")
            self.gpt_client = None
            
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

    async def process_voice(self, file_path: str) -> Dict[str, Any]:
        """Обработка голосового сообщения"""
        try:
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

    async def process_text_message(self, text: str) -> Dict[str, Any]:
        """
        Обрабатывает текстовое сообщение
        
        Args:
            text: Текст для обработки
            
        Returns:
            Результат обработки текстового сообщения
        """
        try:
            logger.info("Processing text message")
            
            # Анализируем текст с помощью парсера
            property_info = self.real_estate_parser.parse_text(text)
            
            # Валидируем информацию
            validation_result = self.real_estate_parser.validate_property_info(property_info)
            
            # Если есть GPT, используем его для улучшения результатов
            gpt_enhanced_info = None
            if self.gpt_client:
                try:
                    gpt_enhanced_info = await self.gpt_client.extract_real_estate_info(text)
                except Exception as e:
                    logger.warning(f"GPT enhancement failed: {e}")
            
            return {
                "original_text": text,
                "property_info": property_info,
                "validation_result": validation_result,
                "gpt_enhanced_info": gpt_enhanced_info
            }
            
        except Exception as e:
            logger.error(f"Error processing text message: {e}")
            return {"error": str(e)}
    
    async def process_mixed_content(self, text: str = "", audio_file_path: str = "", image_file_path: str = "") -> Dict[str, Any]:
        """
        Обрабатывает смешанный контент (текст + аудио + изображение)
        
        Args:
            text: Текстовое сообщение
            audio_file_path: Путь к аудио файлу
            image_file_path: Путь к изображению
            
        Returns:
            Объединенный результат обработки
        """
        try:
            logger.info("Processing mixed content")
            
            results = {
                "text_processing": None,
                "voice_processing": None,
                "image_processing": None,
                "combined_property_info": None
            }
            
            # Обрабатываем текст
            if text:
                results["text_processing"] = await self.process_text_message(text)
            
            # Обрабатываем аудио
            if audio_file_path:
                results["voice_processing"] = await self.process_voice(audio_file_path)
            
            # Обрабатываем изображение
            if image_file_path:
                results["image_processing"] = await self.process_image(image_file_path)
            
            # Объединяем результаты
            combined_info = self._combine_property_info(results)
            results["combined_property_info"] = combined_info
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing mixed content: {e}")
            return {"error": str(e)}
    
    def _combine_property_info(self, results: Dict[str, Any]) -> PropertyInfo:
        """
        Объединяет информацию о недвижимости из разных источников
        
        Args:
            results: Результаты обработки разных типов контента
            
        Returns:
            Объединенная информация о недвижимости
        """
        try:
            combined_info = PropertyInfo()
            sources = []
            
            # Собираем информацию из всех источников
            for source_name, result in results.items():
                if result and "property_info" in result and result["property_info"]:
                    property_info = result["property_info"]
                    sources.append((source_name, property_info))
            
            if not sources:
                return combined_info
            
            # Объединяем информацию, отдавая приоритет более надежным источникам
            # Приоритет: GPT > OCR > Парсер > Голос
            
            # Сортируем источники по приоритету
            source_priority = {
                "gpt_enhanced_info": 4,
                "image_processing": 3,
                "text_processing": 2,
                "voice_processing": 1
            }
            
            sorted_sources = sorted(
                sources,
                key=lambda x: source_priority.get(x[0], 0),
                reverse=True
            )
            
            # Объединяем информацию
            for source_name, property_info in sorted_sources:
                if not combined_info.property_type and property_info.property_type:
                    combined_info.property_type = property_info.property_type
                
                if not combined_info.price and property_info.price:
                    combined_info.price = property_info.price
                
                if not combined_info.area and property_info.area:
                    combined_info.area = property_info.area
                
                if not combined_info.rooms and property_info.rooms is not None:
                    combined_info.rooms = property_info.rooms
                
                if not combined_info.address and property_info.address:
                    combined_info.address = property_info.address
                
                if not combined_info.floor and property_info.floor:
                    combined_info.floor = property_info.floor
                
                if not combined_info.contact and property_info.contact:
                    combined_info.contact = property_info.contact
                
                # Объединяем особенности
                if property_info.features:
                    combined_info.features.extend(property_info.features)
                
                # Берем описание с наивысшим приоритетом
                if not combined_info.description and property_info.description:
                    combined_info.description = property_info.description
            
            # Убираем дубликаты из особенностей
            combined_info.features = list(set(combined_info.features))
            
            # Вычисляем общую уверенность
            total_confidence = sum(info.confidence for _, info in sorted_sources)
            combined_info.confidence = min(total_confidence / len(sorted_sources), 1.0)
            
            return combined_info
            
        except Exception as e:
            logger.error(f"Error combining property info: {e}")
            return PropertyInfo(confidence=0.0) 