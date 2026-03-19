import aiohttp
import logging
from config import CRYPTOBOT_TOKEN, XROCKET_API_KEY

logger = logging.getLogger(__name__)

CRYPTOBOT_API_URL = "https://pay.crypt.bot/api"
XROCKET_API_URL = "https://pay.xrocket.tg"


# ─── CryptoBot ───────────────────────────────────────────────────────────────

async def cryptobot_create_invoice(amount: float, description: str = "Пополнение баланса") -> dict:
    """Create a CryptoBot invoice. Returns dict with invoice_id, pay_url."""
    headers = {"Crypto-Pay-API-Token": CRYPTOBOT_TOKEN}
    payload = {
        "currency_type": "fiat",
        "fiat": "USD",
        "amount": str(amount),
        "description": description,
        "paid_btn_name": "callback",
        "allow_comments": False,
        "allow_anonymous": False,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{CRYPTOBOT_API_URL}/createInvoice",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                data = await response.json()
                if data.get("ok"):
                    result = data["result"]
                    return {
                        "success": True,
                        "invoice_id": str(result["invoice_id"]),
                        "pay_url": result["pay_url"],
                        "amount": amount,
                    }
                else:
                    return {"success": False, "error": data.get("error", {}).get("name", "Unknown")}
    except Exception as e:
        logger.error("CryptoBot create invoice error: %s", e)
        return {"success": False, "error": str(e)}


async def cryptobot_check_invoice(invoice_id: str) -> dict:
    """Check CryptoBot invoice status."""
    headers = {"Crypto-Pay-API-Token": CRYPTOBOT_TOKEN}
    params = {"invoice_ids": invoice_id}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{CRYPTOBOT_API_URL}/getInvoices",
                headers=headers,
                params=params,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                data = await response.json()
                if data.get("ok"):
                    items = data["result"].get("items", [])
                    if items:
                        item = items[0]
                        return {
                            "success": True,
                            "status": item.get("status"),
                            "paid": item.get("status") == "paid",
                            "amount": float(item.get("amount", 0)),
                        }
                    return {"success": False, "error": "Invoice not found"}
                else:
                    return {"success": False, "error": data.get("error", {}).get("name", "Unknown")}
    except Exception as e:
        logger.error("CryptoBot check invoice error: %s", e)
        return {"success": False, "error": str(e)}


# ─── xRocket ─────────────────────────────────────────────────────────────────

async def xrocket_create_invoice(amount: float, description: str = "Пополнение баланса") -> dict:
    """Create an xRocket invoice. Returns dict with invoice_id, pay_url."""
    headers = {
        "Rocket-Pay-Key": XROCKET_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "currency": "USDT",
        "amount": amount,
        "description": description,
        "numPayments": 1,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{XROCKET_API_URL}/tg-invoices",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                data = await response.json()
                if data.get("success"):
                    result = data.get("data", {})
                    return {
                        "success": True,
                        "invoice_id": str(result.get("id")),
                        "pay_url": result.get("link"),
                        "amount": amount,
                    }
                else:
                    return {"success": False, "error": data.get("message", "Unknown error")}
    except Exception as e:
        logger.error("xRocket create invoice error: %s", e)
        return {"success": False, "error": str(e)}


async def xrocket_check_invoice(invoice_id: str) -> dict:
    """Check xRocket invoice status."""
    headers = {"Rocket-Pay-Key": XROCKET_API_KEY}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{XROCKET_API_URL}/tg-invoices/{invoice_id}",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                data = await response.json()
                if data.get("success"):
                    result = data.get("data", {})
                    status = result.get("status")
                    return {
                        "success": True,
                        "status": status,
                        "paid": status == "paid",
                        "amount": float(result.get("amount", 0)),
                    }
                else:
                    return {"success": False, "error": data.get("message", "Unknown error")}
    except Exception as e:
        logger.error("xRocket check invoice error: %s", e)
        return {"success": False, "error": str(e)}
