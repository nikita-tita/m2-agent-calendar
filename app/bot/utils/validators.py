import re
from typing import Optional
from datetime import datetime


def validate_phone(phone: str) -> bool:
    """Валидация номера телефона"""
    # Простая валидация российского номера
    phone_pattern = r'^(\+7|7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$'
    return bool(re.match(phone_pattern, phone))


def validate_email(email: str) -> bool:
    """Валидация email"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))


def validate_price(price: str) -> Optional[int]:
    """Валидация цены"""
    try:
        # Убираем все кроме цифр
        clean_price = re.sub(r'[^\d]', '', price)
        if clean_price:
            return int(clean_price)
    except ValueError:
        pass
    return None


def validate_date(date_str: str) -> Optional[datetime]:
    """Валидация даты"""
    # Различные форматы дат
    date_formats = [
        '%d.%m.%Y',
        '%d.%m.%Y %H:%M',
        '%Y-%m-%d',
        '%Y-%m-%d %H:%M',
        '%d/%m/%Y',
        '%d/%m/%Y %H:%M'
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None


def clean_text(text: str) -> str:
    """Очистка текста от лишних символов"""
    # Убираем множественные пробелы
    text = re.sub(r'\s+', ' ', text)
    # Убираем пробелы в начале и конце
    text = text.strip()
    return text 