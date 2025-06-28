"""
Date utilities
"""
from datetime import datetime, timedelta

def get_week_range(date: datetime):
    """Returns the start and end of the week for a given date."""
    start_of_week = date - timedelta(days=date.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    return start_of_week, end_of_week

def is_work_day(date: datetime):
    """Checks if a given date is a workday (Mon-Fri)."""
    return date.weekday() < 5

def is_work_hours(date: datetime, start_hour=9, end_hour=18):
    """Checks if a given time is within work hours."""
    return start_hour <= date.hour < end_hour 