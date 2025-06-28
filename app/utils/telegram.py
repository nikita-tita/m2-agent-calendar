"""
Telegram Bot Utility
"""
import logging
import asyncio

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, token: str):
        self.token = token
        logger.info("TelegramBot utility initialized.")

    async def send_message(self, chat_id: int, text: str):
        """A mock function to send a message."""
        logger.info(f"Mock sending message to {chat_id}: {text}")
        await asyncio.sleep(0.1) # Simulate network latency
        return {"ok": True, "result": {"message_id": 123}} 