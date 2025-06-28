"""
Упрощённые AI модули
"""
from .nlp import GPTClient
from .speech import WhisperClient
from .vision import OCRClient

__all__ = [
    "GPTClient",
    "WhisperClient", 
    "OCRClient"
]
