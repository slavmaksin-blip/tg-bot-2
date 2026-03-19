import aiohttp
import logging
from config import MAILBUY_API_URL, MAILBUY_TOKEN

logger = logging.getLogger(__name__)

PRICE_MULTIPLIER = 3


async def search_email_by_domain(domain: str) -> dict:
    """
    Search for email by domain via mailbuy API.
    Returns dict with email info or error.
    """
    headers = {
        "Authorization": f"Bearer {MAILBUY_TOKEN}",
        "Content-Type": "application/json",
    }
    params = {"domain": domain}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{MAILBUY_API_URL}/api/search",
                headers=headers,
                params=params,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                data = await response.json()
                if response.status == 200 and data.get("success"):
                    api_price = float(data.get("price", 0))
                    return {
                        "success": True,
                        "domain": domain,
                        "email": data.get("email", "—"),
                        "price": round(api_price * PRICE_MULTIPLIER, 2),
                        "code": data.get("code", "—"),
                        "link": data.get("link", "—"),
                        "status": data.get("status", "active"),
                        "raw": data,
                    }
                else:
                    return {
                        "success": False,
                        "error": data.get("message", "Unknown error"),
                        "raw": data,
                    }
    except aiohttp.ClientError as e:
        logger.error("mailbuy API error: %s", e)
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error("Unexpected mailbuy error: %s", e)
        return {"success": False, "error": str(e)}


async def get_email_message(email: str) -> dict:
    """Retrieve message for a given email address."""
    headers = {
        "Authorization": f"Bearer {MAILBUY_TOKEN}",
        "Content-Type": "application/json",
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{MAILBUY_API_URL}/api/messages",
                headers=headers,
                params={"email": email},
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                data = await response.json()
                if response.status == 200:
                    return {"success": True, "messages": data.get("messages", [])}
                else:
                    return {"success": False, "error": data.get("message", "Unknown error")}
    except Exception as e:
        logger.error("mailbuy message error: %s", e)
        return {"success": False, "error": str(e)}
