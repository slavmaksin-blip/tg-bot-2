import aiohttp
import logging
from config import CRYPTOBOT_TOKEN, XROCKET_API_KEY

logger = logging.getLogger(__name__)

CRYPTOBOT_API_URL = "https://pay.crypt.bot/api"
XROCKET_API_URL = "https://pay.xrocket.tg"


async def create_cryptobot_invoice(amount: float, description: str = "Balance top-up") -> dict:
    url = f"{CRYPTOBOT_API_URL}/createInvoice"
    headers = {"Crypto-Pay-API-Token": CRYPTOBOT_TOKEN}
    payload = {
        "asset": "USDT",
        "amount": str(amount),
        "description": description,
        "expires_in": 3600,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                data = await response.json()
                return data
    except Exception as e:
        logger.error(f"CryptoBot invoice exception: {e}")
        return {"ok": False, "error": str(e)}


async def check_cryptobot_invoice(invoice_id: str) -> dict:
    url = f"{CRYPTOBOT_API_URL}/getInvoices"
    headers = {"Crypto-Pay-API-Token": CRYPTOBOT_TOKEN}
    params = {"invoice_ids": invoice_id}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                data = await response.json()
                return data
    except Exception as e:
        logger.error(f"CryptoBot check invoice exception: {e}")
        return {"ok": False, "error": str(e)}


async def create_xrocket_invoice(amount: float, description: str = "Balance top-up") -> dict:
    url = f"{XROCKET_API_URL}/tg-invoices"
    headers = {
        "Rocket-Pay-Key": XROCKET_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "currency": "USDT",
        "amount": amount,
        "description": description,
        "expiredIn": 3600,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                data = await response.json()
                return data
    except Exception as e:
        logger.error(f"xRocket invoice exception: {e}")
        return {"success": False, "error": str(e)}


async def check_xrocket_invoice(invoice_id: str) -> dict:
    url = f"{XROCKET_API_URL}/tg-invoices/{invoice_id}"
    headers = {"Rocket-Pay-Key": XROCKET_API_KEY}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                data = await response.json()
                return data
    except Exception as e:
        logger.error(f"xRocket check invoice exception: {e}")
        return {"success": False, "error": str(e)}
