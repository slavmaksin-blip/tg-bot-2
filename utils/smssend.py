import aiohttp
import logging
from config import SMSSEND_API_URL, SMSSEND_ACCOUNT, SMSSEND_PASSWORD

logger = logging.getLogger(__name__)


async def send_sms(phone: str, sender: str, message: str) -> dict:
    """
    Send SMS via SMSSEND API.
    Returns dict with 'success' bool and 'message' str.
    """
    params = {
        "account": SMSSEND_ACCOUNT,
        "password": SMSSEND_PASSWORD,
        "to": phone,
        "from": sender,
        "message": message,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{SMSSEND_API_URL}/sendsms",
                params=params,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                text = await response.text()
                if response.status == 200:
                    return {"success": True, "message": text}
                else:
                    return {"success": False, "message": f"HTTP {response.status}: {text}"}
    except aiohttp.ClientError as e:
        logger.error("SMSSEND API error: %s", e)
        return {"success": False, "message": str(e)}
    except Exception as e:
        logger.error("Unexpected SMSSEND error: %s", e)
        return {"success": False, "message": str(e)}
