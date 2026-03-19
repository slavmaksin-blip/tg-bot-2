import aiohttp
import logging
from config import SMSSEND_ACCOUNT, SMSSEND_PASSWORD, SMSSEND_API_URL

logger = logging.getLogger(__name__)

SMSSEND_STATUS_CODES = {
    0: "Успешно",
    -1: "Ошибка аутентификации",
    -2: "IP ограничен",
    -3: "Запрещённые символы",
    -4: "Пустое сообщение",
    -5: "Сообщение слишком длинное",
    -10: "Недостаточно баланса",
    -13: "Пользователь заблокирован",
}


async def send_sms(phone: str, sender: str, text: str) -> dict:
    url = f"{SMSSEND_API_URL}/sendsms"
    params = {
        "account": SMSSEND_ACCOUNT,
        "password": SMSSEND_PASSWORD,
        "smstype": "0",
        "numbers": phone,
        "content": text,
        "sender": sender,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json(content_type=None)
                    return data
                else:
                    logger.error(f"SMSSEND HTTP error: {response.status}")
                    return {"status": -99, "error": f"HTTP {response.status}"}
    except Exception as e:
        logger.error(f"SMSSEND exception: {e}")
        return {"status": -99, "error": str(e)}


async def get_balance() -> dict:
    url = f"{SMSSEND_API_URL}/getbalance"
    params = {
        "account": SMSSEND_ACCOUNT,
        "password": SMSSEND_PASSWORD,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json(content_type=None)
                    return data
                else:
                    return {"status": -99, "error": f"HTTP {response.status}"}
    except Exception as e:
        logger.error(f"SMSSEND balance exception: {e}")
        return {"status": -99, "error": str(e)}
