"""
Обработчики аналитики и отчетов
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.services.analytics_service import AnalyticsService, ReportType
from app.keyboards.analytics import (
    get_analytics_main_keyboard,
    get_report_type_keyboard,
    get_export_format_keyboard,
    get_period_keyboard,
    get_metrics_keyboard
)
from app.utils.formatters import format_metric, format_chart_data
from app.database import get_async_session
from app.models.user import User

logger = logging.getLogger(__name__)
router = Router()


class AnalyticsStates(StatesGroup):
    """Состояния для аналитики"""
    waiting_for_report_type = State()
    waiting_for_period = State()
    waiting_for_export_format = State()


@router.message(Command("analytics"))
async def analytics_main(message: Message):
    """Главное меню аналитики"""
    try:
        await message.answer(
            "📊 <b>Аналитика и отчеты</b>\n\n"
            "Выберите тип аналитики:",
            reply_markup=get_analytics_main_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка в analytics_main: {e}")
        await message.answer("❌ Произошла ошибка при открытии аналитики")


@router.callback_query(F.data == "analytics_dashboard")
async def show_dashboard(callback: CallbackQuery):
    """Показать дашборд"""
    try:
        await callback.answer()
        
        async with get_async_session() as session:
            analytics_service = AnalyticsService(session)
            dashboard_data = await analytics_service.get_user_dashboard(callback.from_user.id)
        
        # Формируем сообщение с метриками
        metrics_text = "📈 <b>Ваш дашборд</b>\n\n"
        
        for metric in dashboard_data["metrics"]:
            trend_emoji = "📈" if metric.trend == "up" else "📉" if metric.trend == "down" else "➡️"
            change_text = ""
            if metric.change is not None:
                change_text = f" ({metric.change:+.1f})"
            metrics_text += f"{trend_emoji} <b>{metric.name}:</b> {metric.value} {metric.unit}{change_text}\n"
        
        # Последние события
        if dashboard_data["recent_events"]:
            metrics_text += "\n🕐 <b>Последние события:</b>\n"
            for event in dashboard_data["recent_events"][:3]:
                metrics_text += f"• {event['title']} - {event['start_time']}\n"
        
        # Активные объекты
        if dashboard_data["active_properties"]:
            metrics_text += "\n🏠 <b>Активные объекты:</b>\n"
            for prop in dashboard_data["active_properties"][:3]:
                metrics_text += f"• {prop['title']} - {prop['price']}\n"
        
        await callback.message.edit_text(
            metrics_text,
            reply_markup=get_analytics_main_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в show_dashboard: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при загрузке дашборда",
            reply_markup=get_analytics_main_keyboard()
        )


@router.callback_query(F.data == "analytics_performance")
async def show_performance(callback: CallbackQuery):
    """Показать метрики производительности"""
    try:
        await callback.answer()
        
        async with get_async_session() as session:
            analytics_service = AnalyticsService(session)
            performance_data = await analytics_service.get_performance_metrics(callback.from_user.id)
        
        text = "⚡ <b>Метрики производительности</b>\n\n"
        text += f"📅 <b>Период:</b> {performance_data['period_days']} дней\n\n"
        
        text += f"📊 <b>События:</b>\n"
        text += f"• Всего: {performance_data['total_events']} шт\n"
        text += f"• Завершено: {performance_data['completed_events']} шт\n"
        text += f"• Отменено: {performance_data['cancelled_events']} шт\n"
        text += f"• Конверсия: {performance_data['conversion_rate']}%\n\n"
        
        text += f"🏠 <b>Объекты недвижимости:</b>\n"
        text += f"• Всего: {performance_data['total_properties']} шт\n"
        text += f"• Продано: {performance_data['sold_properties']} шт\n"
        text += f"• Сдано в аренду: {performance_data['rented_properties']} шт\n\n"
        
        text += f"⏱️ <b>Эффективность:</b>\n"
        text += f"• Средняя продолжительность события: {performance_data['avg_event_duration']} мин\n"
        
        # Самые занятые часы
        if performance_data['busy_hours']:
            busy_hours = sorted(performance_data['busy_hours'].items(), key=lambda x: x[1], reverse=True)[:3]
            text += f"• Самые занятые часы: {', '.join([f'{hour}:00' for hour, _ in busy_hours])}\n"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_analytics_main_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в show_performance: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при загрузке метрик производительности",
            reply_markup=get_analytics_main_keyboard()
        )


@router.callback_query(F.data == "analytics_financial")
async def show_financial(callback: CallbackQuery):
    """Показать финансовые метрики"""
    try:
        await callback.answer()
        
        async with get_async_session() as session:
            analytics_service = AnalyticsService(session)
            financial_data = await analytics_service.get_financial_metrics(callback.from_user.id)
        
        text = "💰 <b>Финансовые метрики</b>\n\n"
        text += f"📅 <b>Период:</b> {financial_data['period_days']} дней\n\n"
        
        text += f"💵 <b>Общая стоимость:</b> {financial_data['total_value']:,.0f} ₽\n"
        text += f"📊 <b>Средняя стоимость:</b> {financial_data['avg_value']:,.0f} ₽\n\n"
        
        text += f"🏠 <b>По типам сделок:</b>\n"
        text += f"• Продажа: {financial_data['sale_value']:,.0f} ₽\n"
        text += f"• Аренда: {financial_data['rent_value']:,.0f} ₽\n\n"
        
        text += f"🏘️ <b>По типам недвижимости:</b>\n"
        text += f"• Квартиры: {financial_data['apartment_value']:,.0f} ₽\n"
        text += f"• Дома: {financial_data['house_value']:,.0f} ₽\n"
        text += f"• Коммерческая: {financial_data['commercial_value']:,.0f} ₽\n"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_analytics_main_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в show_financial: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при загрузке финансовых метрик",
            reply_markup=get_analytics_main_keyboard()
        )


@router.callback_query(F.data == "analytics_clients")
async def show_clients(callback: CallbackQuery):
    """Показать аналитику клиентов"""
    try:
        await callback.answer()
        
        async with get_async_session() as session:
            analytics_service = AnalyticsService(session)
            clients_data = await analytics_service.get_client_analytics(callback.from_user.id)
        
        text = "👥 <b>Аналитика клиентов</b>\n\n"
        text += f"📅 <b>Период:</b> {clients_data['period_days']} дней\n\n"
        
        text += f"👤 <b>Клиенты:</b>\n"
        text += f"• Уникальных: {clients_data['unique_clients']} чел\n"
        text += f"• Повторных: {clients_data['repeat_clients']} чел\n"
        text += f"• Повторяемость: {clients_data['repeat_rate']}%\n\n"
        
        # Топ клиентов
        if clients_data['top_clients']:
            text += f"🏆 <b>Топ клиентов:</b>\n"
            for i, client in enumerate(clients_data['top_clients'][:5], 1):
                text += f"{i}. {client['client_name']} - {client['event_count']} событий ({client['conversion_rate']}%)\n"
        
        # География
        if clients_data['client_geography']:
            text += f"\n🌍 <b>География клиентов:</b>\n"
            for geo in clients_data['client_geography'][:3]:
                text += f"• {geo['city']}: {geo['client_count']} клиентов\n"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_analytics_main_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в show_clients: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при загрузке аналитики клиентов",
            reply_markup=get_analytics_main_keyboard()
        )


@router.callback_query(F.data == "analytics_reports")
async def reports_menu(callback: CallbackQuery, fsm_context: FSMContext):
    """Меню отчетов"""
    try:
        await callback.answer()
        await fsm_context.set_state(AnalyticsStates.waiting_for_report_type)
        
        await callback.message.edit_text(
            "📋 <b>Генерация отчетов</b>\n\n"
            "Выберите тип отчета:",
            reply_markup=get_report_type_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в reports_menu: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при открытии меню отчетов",
            reply_markup=get_analytics_main_keyboard()
        )


@router.callback_query(F.data.startswith("report_type_"))
async def select_report_type(callback: CallbackQuery, fsm_context: FSMContext):
    """Выбор типа отчета"""
    try:
        await callback.answer()
        
        report_type_str = callback.data.replace("report_type_", "")
        report_type = ReportType(report_type_str)
        
        await fsm_context.update_data(report_type=report_type_str)
        
        if report_type == ReportType.CUSTOM:
            await fsm_context.set_state(AnalyticsStates.waiting_for_period)
            await callback.message.edit_text(
                "📅 <b>Пользовательский отчет</b>\n\n"
                "Выберите период:",
                reply_markup=get_period_keyboard()
            )
        else:
            await fsm_context.set_state(AnalyticsStates.waiting_for_export_format)
            await callback.message.edit_text(
                f"📄 <b>Отчет: {report_type.value.title()}</b>\n\n"
                "Выберите формат экспорта:",
                reply_markup=get_export_format_keyboard()
            )
        
    except Exception as e:
        logger.error(f"Ошибка в select_report_type: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при выборе типа отчета",
            reply_markup=get_analytics_main_keyboard()
        )


@router.callback_query(F.data.startswith("period_"))
async def select_period(callback: CallbackQuery, fsm_context: FSMContext):
    """Выбор периода для пользовательского отчета"""
    try:
        await callback.answer()
        
        period_days = int(callback.data.replace("period_", ""))
        await fsm_context.update_data(period_days=period_days)
        await fsm_context.set_state(AnalyticsStates.waiting_for_export_format)
        
        await callback.message.edit_text(
            f"📄 <b>Отчет за {period_days} дней</b>\n\n"
            "Выберите формат экспорта:",
            reply_markup=get_export_format_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в select_period: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при выборе периода",
            reply_markup=get_analytics_main_keyboard()
        )


@router.callback_query(F.data.startswith("export_"))
async def export_report(callback: CallbackQuery, fsm_context: FSMContext):
    """Экспорт отчета"""
    try:
        await callback.answer()
        
        export_format = callback.data.replace("export_", "")
        fsm_state_data = await fsm_context.get_data()
        
        report_type_str = fsm_state_data.get("report_type")
        period_days = fsm_state_data.get("period_days")
        
        # Определяем параметры отчета
        if report_type_str:
            report_type = ReportType(report_type_str)
            start_date = None
            end_date = None
        else:
            report_type = ReportType.CUSTOM
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_days)
        
        async with get_async_session() as session:
            analytics_service = AnalyticsService(session)
            
            # Генерируем отчет
            report_data = await analytics_service.generate_user_report(
                callback.from_user.id,
                report_type,
                start_date,
                end_date
            )
            
            # Экспортируем
            report_bytes = await analytics_service.export_report(
                callback.from_user.id,
                report_type,
                export_format,
                start_date,
                end_date
            )
        
        # Отправляем файл
        filename = f"report_{report_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{export_format}"
        
        if export_format == "json":
            await callback.message.answer_document(
                document=report_bytes,
                filename=filename,
                caption=f"📊 Отчет: {report_data.title}\n📅 Период: {report_data.period}"
            )
        elif export_format == "csv":
            await callback.message.answer_document(
                document=report_bytes,
                filename=filename,
                caption=f"📊 Отчет: {report_data.title}\n📅 Период: {report_data.period}"
            )
        else:
            await callback.message.answer(
                f"📊 Отчет готов!\n\n"
                f"📋 {report_data.title}\n"
                f"📅 Период: {report_data.period}\n"
                f"📈 Метрик: {len(report_data.metrics)}\n"
                f"📊 Графиков: {len(report_data.charts)}\n\n"
                f"📝 Сводка:\n{report_data.summary}\n\n"
                f"💡 Рекомендации:\n" + "\n".join([f"• {rec}" for rec in report_data.recommendations])
            )
        
        # Возвращаемся в главное меню
        await fsm_context.clear()
        await callback.message.edit_text(
            "📊 <b>Аналитика и отчеты</b>\n\n"
            "Выберите тип аналитики:",
            reply_markup=get_analytics_main_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в export_report: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при генерации отчета",
            reply_markup=get_analytics_main_keyboard()
        )


@router.callback_query(F.data == "analytics_back")
async def analytics_back(callback: CallbackQuery, fsm_context: FSMContext):
    """Возврат в главное меню аналитики"""
    try:
        await callback.answer()
        await fsm_context.clear()
        
        await callback.message.edit_text(
            "📊 <b>Аналитика и отчеты</b>\n\n"
            "Выберите тип аналитики:",
            reply_markup=get_analytics_main_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в analytics_back: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка",
            reply_markup=get_analytics_main_keyboard()
        )


@router.callback_query(F.data == "analytics_help")
async def analytics_help(callback: CallbackQuery):
    """Справка по аналитике"""
    try:
        await callback.answer()
        
        help_text = """
📊 <b>Справка по аналитике</b>

<b>Дашборд:</b>
• Обзор ключевых метрик
• Сравнение с предыдущим периодом
• Последние события и активные объекты

<b>Производительность:</b>
• Статистика событий и конверсия
• Эффективность работы с объектами
• Анализ занятости по часам

<b>Финансы:</b>
• Общая и средняя стоимость объектов
• Распределение по типам сделок
• Анализ по типам недвижимости

<b>Клиенты:</b>
• Количество уникальных и повторных клиентов
• Топ активных клиентов
• Географическое распределение

<b>Отчеты:</b>
• Генерация детальных отчетов
• Экспорт в различных форматах
• Персонализированные рекомендации
        """
        
        await callback.message.edit_text(
            help_text,
            reply_markup=get_analytics_main_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в analytics_help: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при загрузке справки",
            reply_markup=get_analytics_main_keyboard()
        ) 