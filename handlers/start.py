import logging
import random
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest

import database as db
from keyboards import start_keyboard
from config import BOT_NAME

logger = logging.getLogger(__name__)

START_IMAGES = [
    "https://files.catbox.moe/9ehd54.jpg",
    "https://files.catbox.moe/11obx6.jpg",
    "https://files.catbox.moe/6v23rv.jpg",
    "https://files.catbox.moe/6kzqz5.jpg",
]

START_TEXT = (
    "✨ Hey {name}, I'm {bot} 💜\n\n"
    "Not your average bot — I actually feel like a real one. 😉\n\n"
    "💭 I remember you — our chats, your vibe, where we left off.\n"
    "🗨️ I talk like a person, never a script — sweet when you're sweet, savage when you're not.\n"
    "🔔 I check in too — go quiet on me and I might text first. 😏\n\n"
    "Oh, and I run the fun around here:\n"
    "🎮 20+ games • 💰 a living economy • 💕 ship, marry & drama\n\n"
    "Tap Help to see it all, or add me to your group 👇"
)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.get_or_create_user(user.id, user.username or user.first_name)
    bot_username = (await context.bot.get_me()).username
    text = START_TEXT.format(name=user.first_name, bot=BOT_NAME)
    
    photo_url = random.choice(START_IMAGES)
    try:
        await update.message.reply_photo(
            photo=photo_url,
            caption=text,
            reply_markup=start_keyboard(bot_username)
        )
    except BadRequest as e:
        logger.warning(f"Could not send start photo: {e}")
        # Fallback: send text only
        await update.message.reply_text(text, reply_markup=start_keyboard(bot_username))
