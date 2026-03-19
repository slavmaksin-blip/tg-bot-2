import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@mensortool")

SMSSEND_ACCOUNT = os.getenv("SMSSEND_ACCOUNT")
SMSSEND_PASSWORD = os.getenv("SMSSEND_PASSWORD")
SMSSEND_API_URL = os.getenv("SMSSEND_API_URL", "http://47.236.91.242:20003")

MAILBUY_API_URL = os.getenv("MAILBUY_API_URL", "http://api.anymessage.shop")
MAILBUY_TOKEN = os.getenv("MAILBUY_TOKEN")

CRYPTOBOT_TOKEN = os.getenv("CRYPTOBOT_TOKEN")
XROCKET_API_KEY = os.getenv("XROCKET_API_KEY")
