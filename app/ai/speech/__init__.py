"""
Speech Recognition модуль

Содержит компоненты для распознавания речи:
- WhisperClient для локального распознавания речи
"""

from .whisper_client import WhisperClient

__all__ = ["WhisperClient"]
