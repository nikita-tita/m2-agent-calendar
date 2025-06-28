"""
API endpoints для аналитики и отчетов
"""
import logging
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.models.user import User
from app.schemas.analytics import (
    AnalyticsRequest,
    AnalyticsResponse,
    ReportRequest,
    ReportResponse,
    DashboardRequest,
    DashboardResponse
)
from app.services.analytics_service import AnalyticsService
from app.core.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    request: DashboardRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Получение дашборда с ключевыми метриками"""
    try:
        analytics_service = AnalyticsService(db)
        
        dashboard_data = await analytics_service.generate_dashboard(
            user_id=current_user.id,
            period=request.period,
            include_properties=request.include_properties,
            include_events=request.include_events,
            include_financial=request.include_financial
        )
        
        return DashboardResponse(**dashboard_data)
        
    except Exception as e:
        logger.error(f"Error generating dashboard: {e}")
        raise HTTPException(status_code=500, detail="Ошибка генерации дашборда")


@router.post("/reports", response_model=ReportResponse)
async def generate_report(
    request: ReportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Генерация отчета"""
    try:
        analytics_service = AnalyticsService(db)
        
        report_data = await analytics_service.generate_report(
            user_id=current_user.id,
            report_type=request.report_type,
            start_date=request.start_date,
            end_date=request.end_date,
            format=request.format,
            filters=request.filters
        )
        
        return ReportResponse(**report_data)
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail="Ошибка генерации отчета")


@router.get("/metrics/properties")
async def get_property_metrics(
    period: str = Query("month", pattern="^(day|week|month|quarter|year)$"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Получение метрик по объектам недвижимости"""
    try:
        analytics_service = AnalyticsService(db)
        
        metrics = await analytics_service.get_property_metrics(
            user_id=current_user.id,
            period=period,
            start_date=start_date,
            end_date=end_date
        )
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting property metrics: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения метрик недвижимости")


@router.get("/metrics/events")
async def get_event_metrics(
    period: str = Query("month", pattern="^(day|week|month|quarter|year)$"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Получение метрик по событиям"""
    try:
        analytics_service = AnalyticsService(db)
        
        metrics = await analytics_service.get_event_metrics(
            user_id=current_user.id,
            period=period,
            start_date=start_date,
            end_date=end_date
        )
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting event metrics: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения метрик событий")


@router.get("/metrics/financial")
async def get_financial_metrics(
    period: str = Query("month", pattern="^(day|week|month|quarter|year)$"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Получение финансовых метрик"""
    try:
        analytics_service = AnalyticsService(db)
        
        metrics = await analytics_service.get_financial_metrics(
            user_id=current_user.id,
            period=period,
            start_date=start_date,
            end_date=end_date
        )
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting financial metrics: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения финансовых метрик")


@router.get("/metrics/clients")
async def get_client_metrics(
    period: str = Query("month", pattern="^(day|week|month|quarter|year)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Получение метрик по клиентам"""
    try:
        analytics_service = AnalyticsService(db)
        
        metrics = await analytics_service.get_client_metrics(
            user_id=current_user.id,
            period=period
        )
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting client metrics: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения метрик клиентов")


@router.get("/trends/properties")
async def get_property_trends(
    trend_type: str = Query("price", pattern="^(price|area|rooms|status)$"),
    period: str = Query("month", pattern="^(day|week|month|quarter|year)$"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Получение трендов по объектам недвижимости"""
    try:
        analytics_service = AnalyticsService(db)
        
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        trends = await analytics_service.get_property_trends(
            user_id=current_user.id,
            trend_type=trend_type,
            period=period,
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "trend_type": trend_type,
            "start_date": start_date,
            "end_date": end_date,
            "trends": trends
        }
        
    except Exception as e:
        logger.error(f"Error getting property trends: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения трендов недвижимости")


@router.get("/trends/events")
async def get_event_trends(
    trend_type: str = Query("count", pattern="^(count|duration|type|status)$"),
    period: str = Query("month", pattern="^(day|week|month|quarter|year)$"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Получение трендов по событиям"""
    try:
        analytics_service = AnalyticsService(db)
        
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        trends = await analytics_service.get_event_trends(
            user_id=current_user.id,
            trend_type=trend_type,
            period=period,
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "trend_type": trend_type,
            "start_date": start_date,
            "end_date": end_date,
            "trends": trends
        }
        
    except Exception as e:
        logger.error(f"Error getting event trends: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения трендов событий")


@router.get("/performance/overview")
async def get_performance_overview(
    period: str = Query("month", pattern="^(week|month|quarter|year)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Получение обзора производительности"""
    try:
        analytics_service = AnalyticsService(db)
        
        overview = await analytics_service.get_performance_overview(
            user_id=current_user.id,
            period=period
        )
        
        return overview
        
    except Exception as e:
        logger.error(f"Error getting performance overview: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения обзора производительности")


@router.get("/performance/indicators")
async def get_performance_indicators(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Получение ключевых показателей эффективности (KPI)"""
    try:
        analytics_service = AnalyticsService(db)
        
        kpis = await analytics_service.get_performance_indicators(
            user_id=current_user.id
        )
        
        return kpis
        
    except Exception as e:
        logger.error(f"Error getting performance indicators: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения показателей эффективности")


@router.get("/comparison/periods")
async def compare_periods(
    current_period: str = Query("month", pattern="^(week|month|quarter|year)$"),
    previous_period: str = Query("month", pattern="^(week|month|quarter|year)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Сравнение показателей за разные периоды"""
    try:
        analytics_service = AnalyticsService(db)
        
        comparison = await analytics_service.compare_periods(
            user_id=current_user.id,
            current_period=current_period,
            previous_period=previous_period
        )
        
        return comparison
        
    except Exception as e:
        logger.error(f"Error comparing periods: {e}")
        raise HTTPException(status_code=500, detail="Ошибка сравнения периодов")


@router.get("/export/data")
async def export_analytics_data(
    data_type: str = Query(..., pattern="^(properties|events|clients|financial)$"),
    format: str = Query("json", pattern="^(json|csv|xlsx)$"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Экспорт аналитических данных"""
    try:
        analytics_service = AnalyticsService(db)
        
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        exported_data = await analytics_service.export_data(
            user_id=current_user.id,
            data_type=data_type,
            format=format,
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "data_type": data_type,
            "format": format,
            "start_date": start_date,
            "end_date": end_date,
            "data": exported_data
        }
        
    except Exception as e:
        logger.error(f"Error exporting analytics data: {e}")
        raise HTTPException(status_code=500, detail="Ошибка экспорта данных")


@router.get("/insights/recommendations")
async def get_insights_and_recommendations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Получение инсайтов и рекомендаций"""
    try:
        analytics_service = AnalyticsService(db)
        
        insights = await analytics_service.get_insights_and_recommendations(
            user_id=current_user.id
        )
        
        return insights
        
    except Exception as e:
        logger.error(f"Error getting insights: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения инсайтов")


@router.get("/forecasts/properties")
async def get_property_forecasts(
    forecast_period: str = Query("month", pattern="^(week|month|quarter|year)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Получение прогнозов по объектам недвижимости"""
    try:
        analytics_service = AnalyticsService(db)
        
        forecasts = await analytics_service.get_property_forecasts(
            user_id=current_user.id,
            forecast_period=forecast_period
        )
        
        return {
            "forecast_period": forecast_period,
            "forecasts": forecasts
        }
        
    except Exception as e:
        logger.error(f"Error getting property forecasts: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения прогнозов недвижимости")


@router.get("/forecasts/events")
async def get_event_forecasts(
    forecast_period: str = Query("month", pattern="^(week|month|quarter|year)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Получение прогнозов по событиям"""
    try:
        analytics_service = AnalyticsService(db)
        
        forecasts = await analytics_service.get_event_forecasts(
            user_id=current_user.id,
            forecast_period=forecast_period
        )
        
        return {
            "forecast_period": forecast_period,
            "forecasts": forecasts
        }
        
    except Exception as e:
        logger.error(f"Error getting event forecasts: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения прогнозов событий")


@router.get("/alerts/thresholds")
async def get_alert_thresholds(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Получение пороговых значений для алертов"""
    try:
        analytics_service = AnalyticsService(db)
        
        thresholds = await analytics_service.get_alert_thresholds(
            user_id=current_user.id
        )
        
        return thresholds
        
    except Exception as e:
        logger.error(f"Error getting alert thresholds: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения пороговых значений")


@router.post("/alerts/thresholds")
async def set_alert_thresholds(
    thresholds: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Установка пороговых значений для алертов"""
    try:
        analytics_service = AnalyticsService(db)
        
        updated_thresholds = await analytics_service.set_alert_thresholds(
            user_id=current_user.id,
            thresholds=thresholds
        )
        
        return {
            "message": "Пороговые значения обновлены",
            "thresholds": updated_thresholds
        }
        
    except Exception as e:
        logger.error(f"Error setting alert thresholds: {e}")
        raise HTTPException(status_code=500, detail="Ошибка установки пороговых значений")


@router.get("/alerts/active")
async def get_active_alerts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Получение активных алертов"""
    try:
        analytics_service = AnalyticsService(db)
        
        alerts = await analytics_service.get_active_alerts(
            user_id=current_user.id
        )
        
        return alerts
        
    except Exception as e:
        logger.error(f"Error getting active alerts: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения активных алертов") 