"""
Pydantic схемы для аутентификации
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator, EmailStr

from app.models.user import User


class UserCreate(BaseModel):
    """Схема для создания пользователя"""
    username: str = Field(..., min_length=3, max_length=50, description="Имя пользователя")
    email: EmailStr = Field(..., description="Email пользователя")
    password: str = Field(..., min_length=6, description="Пароль")
    full_name: Optional[str] = Field(None, max_length=100, description="Полное имя")
    phone: Optional[str] = Field(None, max_length=20, description="Телефон")
    
    @validator('username')
    def validate_username(cls, v):
        if not v.isalnum():
            raise ValueError('Имя пользователя должно содержать только буквы и цифры')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Пароль должен содержать минимум 6 символов')
        return v


class UserLogin(BaseModel):
    """Схема для входа пользователя"""
    username: str = Field(..., description="Имя пользователя или email")
    password: str = Field(..., description="Пароль")


class UserResponse(BaseModel):
    """Схема для ответа с пользователем"""
    id: int
    username: str
    email: str
    full_name: Optional[str]
    phone: Optional[str]
    telegram_id: Optional[int]
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Схема для ответа с токеном"""
    access_token: str
    token_type: str
    expires_in: int  # в секундах


class PasswordChange(BaseModel):
    """Схема для изменения пароля"""
    current_password: str = Field(..., description="Текущий пароль")
    new_password: str = Field(..., min_length=6, description="Новый пароль")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 6:
            raise ValueError('Новый пароль должен содержать минимум 6 символов')
        return v


class PasswordReset(BaseModel):
    """Схема для сброса пароля"""
    email: EmailStr = Field(..., description="Email для сброса пароля")


class UserUpdate(BaseModel):
    """Схема для обновления пользователя"""
    full_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    
    @validator('email')
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Некорректный email')
        return v


class TelegramAuth(BaseModel):
    """Схема для аутентификации через Telegram"""
    telegram_id: int = Field(..., description="ID пользователя в Telegram")
    username: Optional[str] = Field(None, max_length=50)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    photo_url: Optional[str] = Field(None, description="URL фотографии профиля")


class UserProfile(BaseModel):
    """Схема для профиля пользователя"""
    id: int
    username: str
    email: str
    full_name: Optional[str]
    phone: Optional[str]
    telegram_id: Optional[int]
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Дополнительная информация
    total_properties: int = 0
    total_events: int = 0
    last_activity: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserStats(BaseModel):
    """Схема для статистики пользователя"""
    user_id: int
    total_properties: int
    active_properties: int
    total_events: int
    completed_events: int
    total_revenue: float
    registration_date: datetime
    last_activity: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AdminUserCreate(BaseModel):
    """Схема для создания пользователя администратором"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    is_admin: bool = False
    is_active: bool = True
    telegram_id: Optional[int] = None
    
    @validator('username')
    def validate_username(cls, v):
        if not v.isalnum():
            raise ValueError('Имя пользователя должно содержать только буквы и цифры')
        return v


class AdminUserUpdate(BaseModel):
    """Схема для обновления пользователя администратором"""
    full_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None
    telegram_id: Optional[int] = None


class UserListResponse(BaseModel):
    """Схема для ответа со списком пользователей"""
    users: list[UserResponse]
    total: int
    skip: int
    limit: int
    
    class Config:
        from_attributes = True


class SessionInfo(BaseModel):
    """Схема для информации о сессии"""
    user_id: int
    username: str
    is_admin: bool
    login_time: datetime
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    class Config:
        from_attributes = True


class LoginHistory(BaseModel):
    """Схема для истории входов"""
    id: int
    user_id: int
    login_time: datetime
    ip_address: Optional[str]
    user_agent: Optional[str]
    success: bool
    failure_reason: Optional[str] = None
    
    class Config:
        from_attributes = True


class SecuritySettings(BaseModel):
    """Схема для настроек безопасности"""
    password_min_length: int = Field(8, ge=6, le=50)
    require_special_chars: bool = True
    require_numbers: bool = True
    require_uppercase: bool = True
    password_expiry_days: Optional[int] = Field(None, ge=30, le=365)
    max_login_attempts: int = Field(5, ge=3, le=10)
    lockout_duration_minutes: int = Field(30, ge=5, le=1440)
    session_timeout_minutes: int = Field(30, ge=5, le=1440)
    require_email_verification: bool = True
    require_phone_verification: bool = False
    
    class Config:
        from_attributes = True


class EmailVerification(BaseModel):
    """Схема для верификации email"""
    email: EmailStr
    verification_code: str = Field(..., min_length=6, max_length=6)
    
    @validator('verification_code')
    def validate_verification_code(cls, v):
        if not v.isdigit():
            raise ValueError('Код верификации должен содержать только цифры')
        return v


class PhoneVerification(BaseModel):
    """Схема для верификации телефона"""
    phone: str = Field(..., max_length=20)
    verification_code: str = Field(..., min_length=4, max_length=6)
    
    @validator('verification_code')
    def validate_verification_code(cls, v):
        if not v.isdigit():
            raise ValueError('Код верификации должен содержать только цифры')
        return v


class TwoFactorAuth(BaseModel):
    """Схема для двухфакторной аутентификации"""
    enabled: bool = False
    method: Optional[str] = Field(None, pattern="^(email|sms|totp)$")
    backup_codes: Optional[list[str]] = None
    
    class Config:
        from_attributes = True


class TwoFactorVerify(BaseModel):
    """Схема для верификации двухфакторной аутентификации"""
    code: str = Field(..., min_length=6, max_length=6)
    backup_code: Optional[str] = Field(None, min_length=8, max_length=8)
    
    @validator('code')
    def validate_code(cls, v):
        if not v.isdigit():
            raise ValueError('Код должен содержать только цифры')
        return v


class ApiKeyCreate(BaseModel):
    """Схема для создания API ключа"""
    name: str = Field(..., min_length=1, max_length=100, description="Название ключа")
    permissions: list[str] = Field(default_factory=list, description="Разрешения")
    expires_at: Optional[datetime] = Field(None, description="Дата истечения")


class ApiKeyResponse(BaseModel):
    """Схема для ответа с API ключом"""
    id: int
    name: str
    key_prefix: str
    permissions: list[str]
    created_at: datetime
    expires_at: Optional[datetime]
    last_used: Optional[datetime]
    is_active: bool
    
    class Config:
        from_attributes = True


class ApiKeyFullResponse(BaseModel):
    """Схема для ответа с полным API ключом (только при создании)"""
    id: int
    name: str
    api_key: str  # Полный ключ (показывается только один раз)
    permissions: list[str]
    created_at: datetime
    expires_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class TwoFactorAuthRequest(BaseModel):
    """Схема для запроса двухфакторной аутентификации"""
    method: Optional[str] = Field(None, pattern="^(email|sms|totp)$")
    phone: Optional[str] = None
    email: Optional[str] = None
    
    @validator('method')
    def validate_method(cls, v):
        if v and v not in ["email", "sms", "totp"]:
            raise ValueError("Неверный метод двухфакторной аутентификации")
        return v
    
    @validator('phone')
    def validate_phone(cls, v, values):
        if values.get('method') == 'sms' and not v:
            raise ValueError("Номер телефона обязателен для SMS аутентификации")
        return v
    
    @validator('email')
    def validate_email(cls, v, values):
        if values.get('method') == 'email' and not v:
            raise ValueError("Email обязателен для email аутентификации")
        return v 