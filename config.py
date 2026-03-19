import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
ADMIN_ID: int = int(os.getenv("ADMIN_ID", "0"))
CHANNEL_USERNAME: str = os.getenv("CHANNEL_USERNAME", "@mensortool")

SMSSEND_ACCOUNT: str = os.getenv("SMSSEND_ACCOUNT", "")
SMSSEND_PASSWORD: str = os.getenv("SMSSEND_PASSWORD", "")
SMSSEND_API_URL: str = os.getenv("SMSSEND_API_URL", "")

MAILBUY_API_URL: str = os.getenv("MAILBUY_API_URL", "")
MAILBUY_TOKEN: str = os.getenv("MAILBUY_TOKEN", "")

CRYPTOBOT_TOKEN: str = os.getenv("CRYPTOBOT_TOKEN", "")
XROCKET_API_KEY: str = os.getenv("XROCKET_API_KEY", "")

DB_PATH: str = "database.db"
START_PHOTO_PATH: str = "start.jpg"

SUBSCRIPTION_PRICES = {
    1: 6.0,
    3: 12.0,
    15: 28.0,
}
