"""
Система безопасности и защиты данных
"""
import hashlib
import hmac
import secrets
import string
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
import base64
import re
import logging
from functools import wraps
import time
import ipaddress

from app.config import settings
from app.core.exceptions import SecurityException, ValidationException

logger = logging.getLogger(__name__)


class SecurityService:
    """Сервис безопасности"""
    
    def __init__(self):
        self.secret_key = settings.SECRET_KEY.encode()
        self.fernet = Fernet(base64.urlsafe_b64encode(hashlib.sha256(self.secret_key).digest()))
        
        # Генерация RSA ключей
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self.public_key = self.private_key.public_key()
    
    def hash_password(self, password: str, salt: Optional[str] = None) -> Dict[str, str]:
        """Хеширование пароля с солью"""
        if not salt:
            salt = secrets.token_hex(16)
        
        # Использование PBKDF2 для хеширования
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode(),
            iterations=100000,
        )
        
        hash_bytes = kdf.derive(password.encode())
        password_hash = base64.b64encode(hash_bytes).decode()
        
        return {
            "hash": password_hash,
            "salt": salt
        }
    
    def verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """Проверка пароля"""
        try:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt.encode(),
                iterations=100000,
            )
            
            hash_bytes = kdf.derive(password.encode())
            computed_hash = base64.b64encode(hash_bytes).decode()
            
            return hmac.compare_digest(password_hash, computed_hash)
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    def generate_token(self, payload: Dict[str, Any], expires_in: int = 3600) -> str:
        """Генерация JWT токена"""
        payload.update({
            "exp": datetime.utcnow() + timedelta(seconds=expires_in),
            "iat": datetime.utcnow(),
            "jti": secrets.token_hex(16)
        })
        
        return jwt.encode(payload, self.secret_key, algorithm="HS256")
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Проверка JWT токена"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    def encrypt_data(self, data: str) -> str:
        """Шифрование данных"""
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Расшифровка данных"""
        try:
            return self.fernet.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            raise SecurityException("Failed to decrypt data")
    
    def generate_api_key(self, length: int = 32) -> str:
        """Генерация API ключа"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def hash_api_key(self, api_key: str) -> str:
        """Хеширование API ключа для хранения"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def generate_secure_filename(self, original_filename: str) -> str:
        """Генерация безопасного имени файла"""
        # Получение расширения
        ext = ""
        if "." in original_filename:
            ext = "." + original_filename.split(".")[-1]
        
        # Генерация случайного имени
        random_name = secrets.token_hex(16)
        return f"{random_name}{ext}"
    
    def validate_input(self, data: str, max_length: int = 1000) -> str:
        """Валидация и очистка входных данных"""
        if not isinstance(data, str):
            raise ValidationException("Input must be a string")
        
        # Ограничение длины
        if len(data) > max_length:
            raise ValidationException(f"Input too long, max {max_length} characters")
        
        # Удаление потенциально опасных символов
        cleaned = re.sub(r'[<>"\']', '', data)
        
        # Удаление лишних пробелов
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    def sanitize_sql_input(self, data: str) -> str:
        """Очистка данных для SQL запросов"""
        # Удаление SQL инъекций
        dangerous_patterns = [
            r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)',
            r'(\b(OR|AND)\b\s+\d+\s*=\s*\d+)',
            r'(\b(OR|AND)\b\s+\'[^\']*\'\s*=\s*\'[^\']*\')',
            r'(\b(OR|AND)\b\s+\d+\s*=\s*\'[^\']*\')',
            r'(\b(OR|AND)\b\s+\'[^\']*\'\s*=\s*\d+)',
            r'(\b(OR|AND)\b\s+\d+\s*=\s*\d+\s*--\s*)',
            r'(\b(OR|AND)\b\s+\d+\s*=\s*\d+\s*#\s*)',
            r'(\b(OR|AND)\b\s+\d+\s*=\s*\d+\s*/\*)',
            r'(\b(OR|AND)\b\s+\d+\s*=\s*\d+\s*\*/)',
            r'(\b(OR|AND)\b\s+\d+\s*=\s*\d+\s*;\s*)',
            r'(\b(OR|AND)\b\s+\d+\s*=\s*\d+\s*UNION\s*)',
            r'(\b(OR|AND)\b\s+\d+\s*=\s*\d+\s*SELECT\s*)',
            r'(\b(OR|AND)\b\s+\d+\s*=\s*\d+\s*INSERT\s*)',
            r'(\b(OR|AND)\b\s+\d+\s*=\s*\d+\s*UPDATE\s*)',
            r'(\b(OR|AND)\b\s+\d+\s*=\s*\d+\s*DELETE\s*)',
            r'(\b(OR|AND)\b\s+\d+\s*=\s*\d+\s*DROP\s*)',
            r'(\b(OR|AND)\b\s+\d+\s*=\s*\d+\s*CREATE\s*)',
            r'(\b(OR|AND)\b\s+\d+\s*=\s*\d+\s*ALTER\s*)',
            r'(\b(OR|AND)\b\s+\d+\s*=\s*\d+\s*EXEC\s*)',
            r'(\b(OR|AND)\b\s+\d+\s*=\s*\d+\s*UNION\s*ALL\s*)',
            r'(\b(OR|AND)\b\s+\d+\s*=\s*\d+\s*UNION\s*SELECT\s*)',
            r'(\b(OR|AND)\b\s+\d+\s*=\s*\d+\s*UNION\s*ALL\s*SELECT\s*)',
            r'(\b(OR|AND)\b\s+\d+\s*=\s*\d+\s*UNION\s*SELECT\s*NULL\s*)',
            r'(\b(OR|AND)\b\s+\d+\s*=\s*\d+\s*UNION\s*ALL\s*SELECT\s*NULL\s*)',
            r'(\b(OR|AND)\b\s+\d+\s*=\s*\d+\s*UNION\s*SELECT\s*NULL,NULL\s*)',
            r'(\b(OR|AND)\b\s+\d+\s*=\s*\d+\s*UNION\s*ALL\s*SELECT\s*NULL,NULL\s*)',
            r'(\b(OR|AND)\b\s+\d+\s*=\s*\d+\s*UNION\s*SELECT\s*NULL,NULL,NULL\s*)',
            r'(\b(OR|AND)\b\s+\d+\s*=\s*\d+\s*UNION\s*ALL\s*SELECT\s*NULL,NULL,NULL\s*)',
            r'(\b(OR|AND)\b\s+\d+\s*=\s*\d+\s*UNION\s*SELECT\s*NULL,NULL,NULL,NULL\s*)',
            r'(\b(OR|AND)\b\s+\d+\s*=\s*\d+\s*UNION\s*ALL\s*SELECT\s*NULL,NULL,NULL,NULL\s*)',
            r'(\b(OR|AND)\b\s+\d+\s*=\s*\d+\s*UNION\s*SELECT\s*NULL,NULL,NULL,NULL,NULL\s*)',
            r'(\b(OR|AND)\b\s+\d+\s*=\s*\d+\s*UNION\s*ALL\s*SELECT\s*NULL,NULL,NULL,NULL,NULL\s*)',
            r'(\b(OR|AND)\b\s+\d+\s*=\s*\d+\s*UNION\s*SELECT\s*NULL,NULL,NULL,NULL,NULL,NULL\s*)',
            r'(\b(OR|AND)\b\s+\d+\s*=\s*\d+\s*UNION\s*ALL\s*SELECT\s*NULL,NULL,NULL,NULL,NULL,NULL\s*)',
            r'(\b(OR|AND)\b\s+\d+\s*=\s*\d+\s*UNION\s*SELECT\s*NULL,NULL,NULL,NULL,NULL,NULL,NULL\s*)',
            r'(\b(OR|AND)\b\s+\d+\s*=\s*\d+\s*UNION\s*ALL\s*SELECT\s*NULL,NULL,NULL,NULL,NULL,NULL,NULL\s*)',
            r'(\b(OR|AND)\b\s+\d+\s*=\s*\d+\s*UNION\s*SELECT\s*NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL\s*)',
            r'(\b(OR|AND)\b\s+\d+\s*=\s*\d+\s*UNION\s*ALL\s*SELECT\s*NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL\s*)',
            r'(\b(OR|AND)\b\s+\d+\s*=\s*\d+\s*UNION\s*SELECT\s*NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL\s*)',
            r'(\b(OR|AND)\b\s+\d+\s*=\s*\d+\s*UNION\s*ALL\s*SELECT\s*NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL\s*)',
            r'(\b(OR|AND)\b\s+\d+\s*=\s*\d+\s*UNION\s*SELECT\s*NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL\s*)',
            r'(\b(OR|AND)\b\s+\d+\s*=\s*\d+\s*UNION\s*ALL\s*SELECT\s*NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL\s*)',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, data, re.IGNORECASE):
                raise SecurityException("Potential SQL injection detected")
        
        return data


class RateLimiter:
    """Система ограничения скорости запросов"""
    
    def __init__(self):
        self.requests = {}
        self.blocked_ips = {}
    
    def is_rate_limited(self, identifier: str, max_requests: int = 100, window: int = 3600) -> bool:
        """Проверка лимита запросов"""
        current_time = time.time()
        
        # Очистка старых записей
        if identifier in self.requests:
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if current_time - req_time < window
            ]
        else:
            self.requests[identifier] = []
        
        # Проверка лимита
        if len(self.requests[identifier]) >= max_requests:
            return True
        
        # Добавление нового запроса
        self.requests[identifier].append(current_time)
        return False
    
    def block_ip(self, ip: str, duration: int = 3600):
        """Блокировка IP адреса"""
        self.blocked_ips[ip] = time.time() + duration
    
    def is_ip_blocked(self, ip: str) -> bool:
        """Проверка блокировки IP"""
        if ip in self.blocked_ips:
            if time.time() > self.blocked_ips[ip]:
                del self.blocked_ips[ip]
                return False
            return True
        return False


class SecurityMiddleware:
    """Middleware для безопасности"""
    
    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.security_service = SecurityService()
    
    async def process_request(self, request, user_id: Optional[int] = None):
        """Обработка запроса с проверками безопасности"""
        
        # Получение IP адреса
        client_ip = request.client.host if request.client else "unknown"
        
        # Проверка блокировки IP
        if self.rate_limiter.is_ip_blocked(client_ip):
            raise SecurityException("IP address is blocked")
        
        # Проверка лимита запросов
        identifier = f"{client_ip}:{user_id}" if user_id else client_ip
        if self.rate_limiter.is_rate_limited(identifier):
            # Блокировка IP при превышении лимита
            self.rate_limiter.block_ip(client_ip, 3600)
            raise SecurityException("Rate limit exceeded")
        
        # Проверка User-Agent
        user_agent = request.headers.get("user-agent", "")
        if self._is_suspicious_user_agent(user_agent):
            logger.warning(f"Suspicious User-Agent: {user_agent}")
        
        # Проверка заголовков безопасности
        self._validate_security_headers(request.headers)
    
    def _is_suspicious_user_agent(self, user_agent: str) -> bool:
        """Проверка подозрительного User-Agent"""
        suspicious_patterns = [
            r'bot',
            r'crawler',
            r'spider',
            r'scanner',
            r'curl',
            r'wget',
            r'python',
            r'java',
            r'perl',
            r'ruby',
            r'php',
            r'go-http-client',
            r'okhttp',
            r'apache-httpclient',
            r'requests',
            r'urllib',
            r'mechanize',
            r'selenium',
            r'phantomjs',
            r'headless',
            r'automation',
            r'test',
            r'debug',
            r'development',
            r'staging',
            r'localhost',
            r'127\.0\.0\.1',
            r'::1',
            r'0\.0\.0\.0',
        ]
        
        user_agent_lower = user_agent.lower()
        for pattern in suspicious_patterns:
            if re.search(pattern, user_agent_lower):
                return True
        
        return False
    
    def _validate_security_headers(self, headers: Dict[str, str]):
        """Проверка заголовков безопасности"""
        # Проверка Content-Type для POST запросов
        if "content-type" in headers:
            content_type = headers["content-type"].lower()
            if "application/json" not in content_type and "multipart/form-data" not in content_type:
                logger.warning(f"Unexpected Content-Type: {content_type}")


class SecurityDecorator:
    """Декораторы для безопасности"""
    
    @staticmethod
    def require_authentication(func):
        """Декоратор для проверки аутентификации"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Здесь должна быть логика проверки аутентификации
            # Например, проверка токена в заголовках
            return await func(*args, **kwargs)
        return wrapper
    
    @staticmethod
    def require_authorization(permission: str):
        """Декоратор для проверки авторизации"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Здесь должна быть логика проверки авторизации
                # Например, проверка роли пользователя
                return await func(*args, **kwargs)
            return wrapper
        return decorator
    
    @staticmethod
    def validate_input(func):
        """Декоратор для валидации входных данных"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Здесь должна быть логика валидации
            return await func(*args, **kwargs)
        return wrapper
    
    @staticmethod
    def rate_limit(max_requests: int = 100, window: int = 3600):
        """Декоратор для ограничения скорости"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Здесь должна быть логика ограничения скорости
                return await func(*args, **kwargs)
            return wrapper
        return decorator


# Глобальные экземпляры
security_service = SecurityService()
rate_limiter = RateLimiter()
security_middleware = SecurityMiddleware()


class SecurityUtils:
    """Утилиты безопасности"""
    
    @staticmethod
    def generate_secure_password(length: int = 12) -> str:
        """Генерация безопасного пароля"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        while True:
            password = ''.join(secrets.choice(alphabet) for _ in range(length))
            # Проверка сложности
            if (any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and any(c.isdigit() for c in password)
                and any(c in "!@#$%^&*" for c in password)):
                return password
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """Проверка сложности пароля"""
        result = {
            "valid": True,
            "score": 0,
            "issues": []
        }
        
        if len(password) < 8:
            result["valid"] = False
            result["issues"].append("Password too short (minimum 8 characters)")
        
        if not any(c.islower() for c in password):
            result["score"] += 1
            result["issues"].append("No lowercase letters")
        
        if not any(c.isupper() for c in password):
            result["score"] += 1
            result["issues"].append("No uppercase letters")
        
        if not any(c.isdigit() for c in password):
            result["score"] += 1
            result["issues"].append("No digits")
        
        if not any(c in "!@#$%^&*" for c in password):
            result["score"] += 1
            result["issues"].append("No special characters")
        
        if len(password) >= 12:
            result["score"] += 2
        
        return result
    
    @staticmethod
    def is_valid_ip(ip: str) -> bool:
        """Проверка валидности IP адреса"""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def is_private_ip(ip: str) -> bool:
        """Проверка, является ли IP приватным"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            return ip_obj.is_private
        except ValueError:
            return False 