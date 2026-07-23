import os

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
OWNER_ID = int(os.environ.get("OWNER_ID", "0") or "0")

BOT_NAME = os.environ.get("BOT_NAME", "Nova")
DB_PATH = os.environ.get("DB_PATH", "data/nova.db")

# Economy tuning
DAILY_MIN = 200
DAILY_MAX = 800
STARTING_BALANCE = 500
PROTECT_COST = 300
PROTECT_HOURS = 12
REVIVE_COST = 400

# Start photo URL
START_PHOTO = "https://files.catbox.moe/11obx6.jpg"

if not BOT_TOKEN:
    print("[WARN] BOT_TOKEN is not set. The bot will not be able to start.")
