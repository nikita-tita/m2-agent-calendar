import logging
import asyncio
import tempfile
import os
from typing import List, Dict, Any, Optional
import easyocr
import cv2
import numpy as np
from PIL import Image
import io

logger = logging.getLogger(__name__)


class OCRClient:
    """Клиент для распознавания текста с изображений с использованием EasyOCR"""
    
    def __init__(self, languages: List[str] = ["ru", "en"]):
        """
        Args:
            languages: Список языков для распознавания
        """
        self.languages = languages
        self.reader = None
        self._load_reader()
    
    def _load_reader(self) -> None:
        """Загружает EasyOCR reader"""
        try:
            logger.info(f"Loading EasyOCR reader for languages: {self.languages}")
            self.reader = easyocr.Reader(self.languages, gpu=False)  # GPU=False для совместимости
            logger.info("EasyOCR reader loaded successfully")
        except Exception as e:
            logger.error(f"Error loading EasyOCR reader: {e}")
            raise
    
    async def extract_text_from_image(self, image_path: str) -> Dict[str, Any]:
        """
        Извлекает текст из изображения
        
        Args:
            image_path: Путь к изображению
            
        Returns:
            Словарь с извлеченным текстом и метаданными
        """
        try:
            logger.info(f"Extracting text from image: {image_path}")
            
            # Проверяем существование файла
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            # Запускаем OCR в отдельном потоке
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                self._extract_text_sync, 
                image_path
            )
            
            logger.info(f"Text extraction completed: {len(result.get('text', ''))} characters")
            return result
            
        except Exception as e:
            logger.error(f"Error in extract_text_from_image: {e}")
            return {"error": str(e), "text": "", "confidence": 0.0}
    
    def _extract_text_sync(self, image_path: str) -> Dict[str, Any]:
        """Синхронное извлечение текста (выполняется в executor)"""
        try:
            # Читаем изображение
            results = self.reader.readtext(image_path)
            
            # Извлекаем текст и координаты
            extracted_text = []
            text_blocks = []
            total_confidence = 0.0
            valid_results = 0
            
            for (bbox, text, confidence) in results:
                if confidence > 0.3:  # Фильтруем результаты с низкой уверенностью
                    extracted_text.append(text)
                    text_blocks.append({
                        "text": text,
                        "confidence": confidence,
                        "bbox": bbox
                    })
                    total_confidence += confidence
                    valid_results += 1
            
            # Объединяем текст
            full_text = " ".join(extracted_text)
            
            # Вычисляем среднюю уверенность
            avg_confidence = total_confidence / valid_results if valid_results > 0 else 0.0
            
            return {
                "text": full_text,
                "confidence": avg_confidence,
                "text_blocks": text_blocks,
                "total_blocks": len(text_blocks),
                "image_path": image_path
            }
            
        except Exception as e:
            logger.error(f"Error in _extract_text_sync: {e}")
            raise
    
    async def extract_text_from_bytes(self, image_bytes: bytes, file_extension: str = "jpg") -> Dict[str, Any]:
        """
        Извлекает текст из изображения в байтах
        
        Args:
            image_bytes: Изображение в байтах
            file_extension: Расширение файла
            
        Returns:
            Словарь с извлеченным текстом и метаданными
        """
        try:
            # Создаем временный файл
            with tempfile.NamedTemporaryFile(
                suffix=f".{file_extension}", 
                delete=False
            ) as temp_file:
                temp_file.write(image_bytes)
                temp_file_path = temp_file.name
            
            try:
                # Извлекаем текст
                result = await self.extract_text_from_image(temp_file_path)
                return result
            finally:
                # Удаляем временный файл
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            logger.error(f"Error in extract_text_from_bytes: {e}")
            return {"error": str(e), "text": "", "confidence": 0.0}
    
    async def extract_real_estate_info_from_image(self, image_path: str) -> Dict[str, Any]:
        """
        Специализированное извлечение информации о недвижимости из изображения
        
        Args:
            image_path: Путь к изображению
            
        Returns:
            Структурированная информация о недвижимости
        """
        try:
            logger.info(f"Extracting real estate info from image: {image_path}")
            
            # Извлекаем весь текст
            ocr_result = await self.extract_text_from_image(image_path)
            
            if "error" in ocr_result:
                return ocr_result
            
            text = ocr_result.get("text", "")
            
            # Анализируем текст на предмет информации о недвижимости
            real_estate_info = self._analyze_real_estate_text(text)
            
            return {
                "ocr_result": ocr_result,
                "real_estate_info": real_estate_info,
                "image_path": image_path
            }
            
        except Exception as e:
            logger.error(f"Error in extract_real_estate_info_from_image: {e}")
            return {"error": str(e)}
    
    def _analyze_real_estate_text(self, text: str) -> Dict[str, Any]:
        """
        Анализирует текст на предмет информации о недвижимости
        
        Args:
            text: Текст для анализа
            
        Returns:
            Структурированная информация о недвижимости
        """
        try:
            import re
            
            info = {
                "property_type": None,
                "price": None,
                "area": None,
                "rooms": None,
                "address": None,
                "floor": None,
                "description": text[:200] if text else None  # Первые 200 символов как описание
            }
            
            # Поиск цены (рубли)
            price_patterns = [
                r'(\d{1,3}(?:\s\d{3})*)\s*(?:руб|₽|рубл)',
                r'(?:цена|стоимость|от|до)\s*(\d{1,3}(?:\s\d{3})*)',
                r'(\d{1,3}(?:\s\d{3})*)\s*(?:тыс|т\.р|тысяч)'
            ]
            
            for pattern in price_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    price_str = match.group(1).replace(" ", "")
                    try:
                        info["price"] = int(price_str)
                        break
                    except:
                        continue
            
            # Поиск площади
            area_patterns = [
                r'(\d+(?:[.,]\d+)?)\s*(?:кв\.м|м²|кв\s*м)',
                r'(?:площадь|S)\s*(\d+(?:[.,]\d+)?)',
                r'(\d+(?:[.,]\d+)?)\s*(?:кв|м2)'
            ]
            
            for pattern in area_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    area_str = match.group(1).replace(",", ".")
                    try:
                        info["area"] = float(area_str)
                        break
                    except:
                        continue
            
            # Поиск количества комнат
            rooms_patterns = [
                r'(\d+)\s*(?:комн|комнат|к)',
                r'(?:студия|1|2|3|4|5)\s*(?:комн|комнат)',
                r'(?:одно|двух|трех|четырех|пяти)\s*(?:комнатн)'
            ]
            
            for pattern in rooms_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    if "студия" in match.group(0).lower():
                        info["rooms"] = 0
                    else:
                        try:
                            info["rooms"] = int(match.group(1))
                            break
                        except:
                            continue
            
            # Поиск типа недвижимости
            property_types = {
                "квартира": ["квартира", "кв", "апартаменты"],
                "дом": ["дом", "коттедж", "дача", "усадьба"],
                "коммерческая": ["офис", "магазин", "склад", "помещение", "коммерческая"]
            }
            
            text_lower = text.lower()
            for prop_type, keywords in property_types.items():
                if any(keyword in text_lower for keyword in keywords):
                    info["property_type"] = prop_type
                    break
            
            # Поиск этажа
            floor_patterns = [
                r'(\d+)\s*(?:этаж|эт)',
                r'(?:этаж|эт)\s*(\d+)',
                r'(\d+)/(\d+)'  # формат "5/9"
            ]
            
            for pattern in floor_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    try:
                        if "/" in match.group(0):
                            # Формат "5/9" - берем первый номер
                            info["floor"] = int(match.group(1))
                        else:
                            info["floor"] = int(match.group(1))
                        break
                    except:
                        continue
            
            return info
            
        except Exception as e:
            logger.error(f"Error in _analyze_real_estate_text: {e}")
            return {"error": str(e)}
    
    async def is_image_valid(self, image_path: str) -> bool:
        """
        Проверяет, подходит ли изображение для обработки
        
        Args:
            image_path: Путь к изображению
            
        Returns:
            True если изображение подходит для обработки
        """
        try:
            if not os.path.exists(image_path):
                return False
            
            # Проверяем размер файла (не более 10MB)
            file_size = os.path.getsize(image_path)
            if file_size > 10 * 1024 * 1024:  # 10MB
                logger.warning(f"Image file too large: {file_size} bytes")
                return False
            
            # Проверяем расширение файла
            supported_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
            file_extension = os.path.splitext(image_path)[1].lower()
            
            if file_extension not in supported_extensions:
                logger.warning(f"Unsupported image format: {file_extension}")
                return False
            
            # Проверяем, что файл является валидным изображением
            try:
                with Image.open(image_path) as img:
                    img.verify()
                return True
            except Exception:
                logger.warning(f"Invalid image file: {image_path}")
                return False
            
        except Exception as e:
            logger.error(f"Error checking image validity: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Возвращает информацию о модели"""
        return {
            "languages": self.languages,
            "reader_loaded": self.reader is not None,
            "supported_formats": ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'],
            "max_file_size": "10MB",
            "confidence_threshold": 0.3
        } 