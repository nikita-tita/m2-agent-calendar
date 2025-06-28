"""
Pydantic схемы для аналитики и отчетов
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class PeriodType(str, Enum):
    """Типы периодов для аналитики"""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


class ReportType(str, Enum):
    """Типы отчетов"""
    PROPERTY_SUMMARY = "property_summary"
    EVENT_SUMMARY = "event_summary"
    FINANCIAL_REPORT = "financial_report"
    CLIENT_ANALYSIS = "client_analysis"
    PERFORMANCE_REPORT = "performance_report"
    COMPARATIVE_ANALYSIS = "comparative_analysis"


class ExportFormat(str, Enum):
    """Форматы экспорта"""
    JSON = "json"
    CSV = "csv"
    XLSX = "xlsx"
    PDF = "pdf"


class AnalyticsRequest(BaseModel):
    """Схема для запроса аналитики"""
    period: PeriodType = Field(..., description="Период анализа")
    start_date: Optional[datetime] = Field(None, description="Начальная дата")
    end_date: Optional[datetime] = Field(None, description="Конечная дата")
    filters: Optional[Dict[str, Any]] = Field(None, description="Фильтры")
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v and values.get('start_date') and v <= values['start_date']:
            raise ValueError('Конечная дата должна быть позже начальной')
        return v


class AnalyticsResponse(BaseModel):
    """Схема для ответа аналитики"""
    period: PeriodType
    start_date: datetime
    end_date: datetime
    metrics: Dict[str, Any]
    trends: List[Dict[str, Any]]
    insights: List[str]
    generated_at: datetime
    
    class Config:
        from_attributes = True


class ReportRequest(BaseModel):
    """Схема для запроса отчета"""
    report_type: ReportType = Field(..., description="Тип отчета")
    start_date: datetime = Field(..., description="Начальная дата")
    end_date: datetime = Field(..., description="Конечная дата")
    format: ExportFormat = Field(ExportFormat.JSON, description="Формат отчета")
    filters: Optional[Dict[str, Any]] = Field(None, description="Фильтры")
    include_charts: bool = Field(True, description="Включить графики")
    include_details: bool = Field(True, description="Включить детали")
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('Конечная дата должна быть позже начальной')
        return v


class ReportResponse(BaseModel):
    """Схема для ответа отчета"""
    report_type: ReportType
    start_date: datetime
    end_date: datetime
    format: ExportFormat
    content: Dict[str, Any]
    summary: Dict[str, Any]
    charts: Optional[List[Dict[str, Any]]] = None
    generated_at: datetime
    file_url: Optional[str] = None
    
    class Config:
        from_attributes = True


class DashboardRequest(BaseModel):
    """Схема для запроса дашборда"""
    period: PeriodType = Field(PeriodType.MONTH, description="Период")
    include_properties: bool = Field(True, description="Включить метрики недвижимости")
    include_events: bool = Field(True, description="Включить метрики событий")
    include_financial: bool = Field(True, description="Включить финансовые метрики")
    include_clients: bool = Field(True, description="Включить метрики клиентов")


class DashboardResponse(BaseModel):
    """Схема для ответа дашборда"""
    period: PeriodType
    generated_at: datetime
    
    # Основные метрики
    total_properties: int
    active_properties: int
    total_events: int
    completed_events: int
    total_revenue: float
    average_property_price: float
    
    # Детальные метрики
    property_metrics: Optional[Dict[str, Any]] = None
    event_metrics: Optional[Dict[str, Any]] = None
    financial_metrics: Optional[Dict[str, Any]] = None
    client_metrics: Optional[Dict[str, Any]] = None
    
    # Тренды
    trends: List[Dict[str, Any]]
    
    # Инсайты
    insights: List[str]
    
    class Config:
        from_attributes = True


class MetricValue(BaseModel):
    """Схема для значения метрики"""
    value: float
    unit: Optional[str] = None
    change_percent: Optional[float] = None
    trend: Optional[str] = None  # "up", "down", "stable"
    
    class Config:
        from_attributes = True


class PropertyMetrics(BaseModel):
    """Схема для метрик недвижимости"""
    total_count: int
    active_count: int
    sold_count: int
    rented_count: int
    average_price: MetricValue
    average_area: MetricValue
    popular_districts: List[Dict[str, Any]]
    property_type_distribution: Dict[str, int]
    deal_type_distribution: Dict[str, int]
    price_range: Dict[str, float]
    
    class Config:
        from_attributes = True


class EventMetrics(BaseModel):
    """Схема для метрик событий"""
    total_count: int
    completed_count: int
    cancelled_count: int
    upcoming_count: int
    average_duration: MetricValue
    events_by_type: Dict[str, int]
    events_by_status: Dict[str, int]
    busy_hours: Dict[str, int]
    popular_locations: List[Dict[str, Any]]
    
    class Config:
        from_attributes = True


class FinancialMetrics(BaseModel):
    """Схема для финансовых метрик"""
    total_revenue: MetricValue
    total_expenses: MetricValue
    net_profit: MetricValue
    profit_margin: MetricValue
    average_commission: MetricValue
    revenue_by_month: List[Dict[str, Any]]
    expense_categories: Dict[str, float]
    
    class Config:
        from_attributes = True


class ClientMetrics(BaseModel):
    """Схема для метрик клиентов"""
    total_clients: int
    new_clients: int
    active_clients: int
    average_client_value: MetricValue
    client_satisfaction: MetricValue
    client_retention_rate: MetricValue
    top_clients: List[Dict[str, Any]]
    client_segments: Dict[str, int]
    
    class Config:
        from_attributes = True


class TrendData(BaseModel):
    """Схема для данных тренда"""
    date: datetime
    value: float
    change: Optional[float] = None
    change_percent: Optional[float] = None
    
    class Config:
        from_attributes = True


class TrendAnalysis(BaseModel):
    """Схема для анализа тренда"""
    metric_name: str
    period: PeriodType
    data: List[TrendData]
    overall_trend: str  # "increasing", "decreasing", "stable"
    trend_strength: float  # от 0 до 1
    seasonality: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class PerformanceIndicator(BaseModel):
    """Схема для показателя эффективности"""
    name: str
    value: float
    target: Optional[float] = None
    unit: Optional[str] = None
    status: str  # "excellent", "good", "average", "poor"
    description: str
    
    class Config:
        from_attributes = True


class PerformanceOverview(BaseModel):
    """Схема для обзора производительности"""
    period: PeriodType
    overall_score: float
    indicators: List[PerformanceIndicator]
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    
    class Config:
        from_attributes = True


class ComparisonData(BaseModel):
    """Схема для данных сравнения"""
    current_period: Dict[str, Any]
    previous_period: Dict[str, Any]
    changes: Dict[str, float]
    change_percentages: Dict[str, float]
    significant_changes: List[str]
    
    class Config:
        from_attributes = True


class ForecastData(BaseModel):
    """Схема для данных прогноза"""
    metric: str
    forecast_period: PeriodType
    predictions: List[Dict[str, Any]]
    confidence_interval: Dict[str, float]
    accuracy_score: float
    factors: List[str]
    
    class Config:
        from_attributes = True


class AlertThreshold(BaseModel):
    """Схема для порога алерта"""
    metric: str
    operator: str  # ">", "<", ">=", "<=", "=="
    value: float
    enabled: bool = True
    notification_channels: List[str] = ["telegram"]
    
    class Config:
        from_attributes = True


class Alert(BaseModel):
    """Схема для алерта"""
    id: int
    metric: str
    current_value: float
    threshold_value: float
    severity: str  # "low", "medium", "high", "critical"
    message: str
    created_at: datetime
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class Insight(BaseModel):
    """Схема для инсайта"""
    id: int
    title: str
    description: str
    category: str  # "performance", "trend", "opportunity", "risk"
    confidence: float  # от 0 до 1
    impact: str  # "high", "medium", "low"
    recommendations: List[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ExportRequest(BaseModel):
    """Схема для запроса экспорта"""
    data_type: str = Field(..., pattern="^(properties|events|clients|financial|analytics)$")
    format: ExportFormat = Field(ExportFormat.JSON)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    filters: Optional[Dict[str, Any]] = None
    include_metadata: bool = True
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        if v and values.get('start_date') and v <= values['start_date']:
            raise ValueError('Конечная дата должна быть позже начальной')
        return v


class ExportResponse(BaseModel):
    """Схема для ответа экспорта"""
    data_type: str
    format: ExportFormat
    file_url: str
    file_size: int
    record_count: int
    exported_at: datetime
    expires_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ChartData(BaseModel):
    """Схема для данных графика"""
    chart_type: str  # "line", "bar", "pie", "scatter"
    title: str
    data: List[Dict[str, Any]]
    options: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class AnalyticsFilter(BaseModel):
    """Схема для фильтра аналитики"""
    property_types: Optional[List[str]] = None
    event_types: Optional[List[str]] = None
    date_range: Optional[Dict[str, datetime]] = None
    price_range: Optional[Dict[str, float]] = None
    locations: Optional[List[str]] = None
    clients: Optional[List[str]] = None
    statuses: Optional[List[str]] = None
    
    @validator('date_range')
    def validate_date_range(cls, v):
        if v and 'start' in v and 'end' in v and v['end'] <= v['start']:
            raise ValueError('Конечная дата должна быть позже начальной')
        return v
    
    @validator('price_range')
    def validate_price_range(cls, v):
        if v and 'min' in v and 'max' in v and v['max'] < v['min']:
            raise ValueError('Максимальная цена не может быть меньше минимальной')
        return v 