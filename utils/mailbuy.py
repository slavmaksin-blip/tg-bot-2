import aiohttp
import asyncio
import logging
from config import MAILBUY_API_URL, MAILBUY_TOKEN

logger = logging.getLogger(__name__)


async def order_email(domain: str, site: str = "mailcom") -> dict:
    url = f"{MAILBUY_API_URL}/email/order"
    params = {
        "token": MAILBUY_TOKEN,
        "site": site,
        "domain": domain,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                data = await response.json(content_type=None)
                return data
    except Exception as e:
        logger.error(f"mailbuy order exception: {e}")
        return {"status": "error", "value": str(e)}


async def get_message(order_id: str, preview: int = 0, max_retries: int = 5) -> dict:
    url = f"{MAILBUY_API_URL}/email/getmessage"
    params = {
        "token": MAILBUY_TOKEN,
        "id": order_id,
    }
    if preview:
        params["preview"] = "1"

    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    data = await response.json(content_type=None)
                    if data.get("status") == "error" and data.get("value") == "wait message":
                        if attempt < max_retries - 1:
                            await asyncio.sleep(3)
                            continue
                    return data
        except Exception as e:
            logger.error(f"mailbuy getmessage exception: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(3)
            else:
                return {"status": "error", "value": str(e)}
    return {"status": "error", "value": "Max retries exceeded"}


async def reorder_email(order_id: str) -> dict:
    url = f"{MAILBUY_API_URL}/email/reorder"
    params = {
        "token": MAILBUY_TOKEN,
        "id": order_id,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                data = await response.json(content_type=None)
                return data
    except Exception as e:
        logger.error(f"mailbuy reorder exception: {e}")
        return {"status": "error", "value": str(e)}


async def cancel_email(order_id: str) -> dict:
    url = f"{MAILBUY_API_URL}/email/cancel"
    params = {
        "token": MAILBUY_TOKEN,
        "id": order_id,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                data = await response.json(content_type=None)
                return data
    except Exception as e:
        logger.error(f"mailbuy cancel exception: {e}")
        return {"status": "error", "value": str(e)}
