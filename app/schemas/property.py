"""
Pydantic схемы для объектов недвижимости
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum

from app.models.property import PropertyType, PropertyStatus, DealType


class PropertyCreate(BaseModel):
    """Схема для создания объекта недвижимости"""
    title: str = Field(..., min_length=1, max_length=200, description="Название объекта")
    description: Optional[str] = Field(None, max_length=2000, description="Описание объекта")
    property_type: PropertyType = Field(..., description="Тип недвижимости")
    deal_type: DealType = Field(..., description="Тип сделки")
    price: Optional[float] = Field(None, ge=0, description="Цена")
    area: Optional[float] = Field(None, ge=0, description="Площадь в кв.м")
    rooms: Optional[int] = Field(None, ge=0, description="Количество комнат")
    floor: Optional[int] = Field(None, ge=0, description="Этаж")
    total_floors: Optional[int] = Field(None, ge=0, description="Всего этажей")
    address: Optional[str] = Field(None, max_length=500, description="Адрес")
    city: Optional[str] = Field(None, max_length=100, description="Город")
    district: Optional[str] = Field(None, max_length=100, description="Район")
    metro_station: Optional[str] = Field(None, max_length=100, description="Станция метро")
    
    @validator('price')
    def validate_price(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Цена должна быть положительной')
        return v
    
    @validator('area')
    def validate_area(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Площадь должна быть положительной')
        return v
    
    @validator('rooms')
    def validate_rooms(cls, v):
        if v is not None and v < 0:
            raise ValueError('Количество комнат не может быть отрицательным')
        return v
    
    @validator('floor')
    def validate_floor(cls, v, values):
        if v is not None and values.get('total_floors') is not None:
            if v > values['total_floors']:
                raise ValueError('Этаж не может быть больше общего количества этажей')
        return v


class PropertyUpdate(BaseModel):
    """Схема для обновления объекта недвижимости"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    property_type: Optional[PropertyType] = None
    deal_type: Optional[DealType] = None
    price: Optional[float] = Field(None, ge=0)
    area: Optional[float] = Field(None, ge=0)
    rooms: Optional[int] = Field(None, ge=0)
    floor: Optional[int] = Field(None, ge=0)
    total_floors: Optional[int] = Field(None, ge=0)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    district: Optional[str] = Field(None, max_length=100)
    metro_station: Optional[str] = Field(None, max_length=100)
    status: Optional[PropertyStatus] = None
    
    @validator('price')
    def validate_price(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Цена должна быть положительной')
        return v
    
    @validator('area')
    def validate_area(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Площадь должна быть положительной')
        return v
    
    @validator('rooms')
    def validate_rooms(cls, v):
        if v is not None and v < 0:
            raise ValueError('Количество комнат не может быть отрицательным')
        return v


class PropertyResponse(BaseModel):
    """Схема для ответа с объектом недвижимости"""
    id: int
    title: str
    description: Optional[str]
    property_type: PropertyType
    deal_type: DealType
    price: Optional[float]
    area: Optional[float]
    rooms: Optional[int]
    floor: Optional[int]
    total_floors: Optional[int]
    address: Optional[str]
    city: Optional[str]
    district: Optional[str]
    metro_station: Optional[str]
    status: PropertyStatus
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True
    
    @property
    def price_formatted(self) -> str:
        """Форматированная цена"""
        if self.price is None:
            return "Цена не указана"
        return f"{self.price:,.0f} ₽"
    
    @property
    def area_formatted(self) -> str:
        """Форматированная площадь"""
        if self.area is None:
            return "Площадь не указана"
        return f"{self.area} кв.м"


class PropertyListResponse(BaseModel):
    """Схема для ответа со списком объектов недвижимости"""
    properties: List[PropertyResponse]
    total: int
    skip: int
    limit: int
    
    class Config:
        from_attributes = True


class PropertyFilter(BaseModel):
    """Схема для фильтрации объектов недвижимости"""
    status: Optional[PropertyStatus] = None
    property_type: Optional[PropertyType] = None
    deal_type: Optional[DealType] = None
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    min_area: Optional[float] = Field(None, ge=0)
    max_area: Optional[float] = Field(None, ge=0)
    min_rooms: Optional[int] = Field(None, ge=0)
    max_rooms: Optional[int] = Field(None, ge=0)
    city: Optional[str] = None
    district: Optional[str] = None
    metro_station: Optional[str] = None
    
    @validator('max_price')
    def validate_max_price(cls, v, values):
        if v is not None and values.get('min_price') is not None:
            if v < values['min_price']:
                raise ValueError('Максимальная цена не может быть меньше минимальной')
        return v
    
    @validator('max_area')
    def validate_max_area(cls, v, values):
        if v is not None and values.get('min_area') is not None:
            if v < values['min_area']:
                raise ValueError('Максимальная площадь не может быть меньше минимальной')
        return v
    
    @validator('max_rooms')
    def validate_max_rooms(cls, v, values):
        if v is not None and values.get('min_rooms') is not None:
            if v < values['min_rooms']:
                raise ValueError('Максимальное количество комнат не может быть меньше минимального')
        return v


class PropertyStatistics(BaseModel):
    """Схема для статистики объектов недвижимости"""
    total_properties: int
    status_distribution: dict
    type_distribution: dict
    deal_type_distribution: dict
    total_value: float
    average_price: Optional[float] = None
    average_area: Optional[float] = None
    
    class Config:
        from_attributes = True


class PropertySearchRequest(BaseModel):
    """Схема для поиска объектов недвижимости"""
    query: str = Field(..., min_length=1, max_length=500, description="Поисковый запрос")
    filters: Optional[PropertyFilter] = None
    sort_by: Optional[str] = Field(None, description="Поле для сортировки")
    sort_order: Optional[str] = Field("asc", pattern="^(asc|desc)$", description="Порядок сортировки")
    page: int = Field(1, ge=1, description="Номер страницы")
    page_size: int = Field(20, ge=1, le=100, description="Размер страницы")


class PropertySearchResponse(BaseModel):
    """Схема для ответа поиска объектов недвижимости"""
    properties: List[PropertyResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    query: str
    
    class Config:
        from_attributes = True


class PropertyBulkUpdate(BaseModel):
    """Схема для массового обновления объектов недвижимости"""
    property_ids: List[int] = Field(..., min_items=1, description="ID объектов для обновления")
    updates: PropertyUpdate = Field(..., description="Данные для обновления")
    
    @validator('property_ids')
    def validate_property_ids(cls, v):
        if len(set(v)) != len(v):
            raise ValueError('ID объектов должны быть уникальными')
        return v


class PropertyExportRequest(BaseModel):
    """Схема для экспорта объектов недвижимости"""
    format: str = Field(..., pattern="^(json|csv|xlsx)$", description="Формат экспорта")
    filters: Optional[PropertyFilter] = None
    include_photos: bool = Field(False, description="Включить фотографии")
    include_statistics: bool = Field(True, description="Включить статистику")


class PropertyImportRequest(BaseModel):
    """Схема для импорта объектов недвижимости"""
    file: str = Field(..., description="Путь к файлу для импорта")
    format: str = Field(..., pattern="^(json|csv|xlsx)$", description="Формат файла")
    update_existing: bool = Field(False, description="Обновлять существующие объекты")
    skip_duplicates: bool = Field(True, description="Пропускать дубликаты")


class PropertyPhotoUpload(BaseModel):
    """Схема для загрузки фотографий"""
    property_id: int = Field(..., description="ID объекта недвижимости")
    photos: List[str] = Field(..., min_items=1, description="Список путей к фотографиям")
    is_primary: Optional[int] = Field(None, description="Индекс главной фотографии")
    
    @validator('is_primary')
    def validate_primary_photo(cls, v, values):
        if v is not None and 'photos' in values:
            if v < 0 or v >= len(values['photos']):
                raise ValueError('Индекс главной фотографии должен быть в пределах списка фотографий')
        return v


class PropertyPhotoResponse(BaseModel):
    """Схема для ответа с фотографией объекта"""
    id: int
    property_id: int
    url: str
    filename: str
    is_primary: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class PropertyAnalytics(BaseModel):
    """Схема для аналитики объектов недвижимости"""
    total_properties: int
    active_properties: int
    sold_properties: int
    rented_properties: int
    total_value: float
    average_price: float
    price_range: dict
    area_range: dict
    popular_districts: List[dict]
    popular_metro_stations: List[dict]
    property_type_distribution: dict
    deal_type_distribution: dict
    monthly_trends: List[dict]
    
    class Config:
        from_attributes = True 