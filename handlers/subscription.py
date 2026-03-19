from aiogram import Bot
from config import CHANNEL_USERNAME
import logging

logger = logging.getLogger(__name__)


async def check_subscription(bot: Bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status not in ["left", "kicked", "banned", "restricted"]
    except Exception as e:
        logger.error(f"Error checking subscription for {user_id}: {e}")
        return False
