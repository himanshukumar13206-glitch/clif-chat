import random

from telegram import Update
from telegram.ext import ContextTypes

import database as db
from persona import chat_reply
from config import BOT_NAME

REACTION_EMOJIS = ["❤️", "😂", "🔥", "😉", "💜", "👀"]


async def checkins_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not context.args or context.args[0].lower() not in ("on", "off"):
        await update.message.reply_text("Usage: /checkins on|off")
        return
    on = context.args[0].lower() == "on"
    db.set_pref(user.id, "checkins", 1 if on else 0)
    await update.message.reply_text(f"🔔 Check-ins {'enabled' if on else 'disabled'}.")


async def reactions_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not context.args or context.args[0].lower() not in ("on", "off"):
        await update.message.reply_text("Usage: /reactions on|off")
        return
    on = context.args[0].lower() == "on"
    db.set_pref(user.id, "reactions", 1 if on else 0)
    await update.message.reply_text(f"😄 Reactions {'enabled' if on else 'disabled'}.")


async def quiet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.set_pref(update.effective_user.id, "personal_mode", "quiet")
    await update.message.reply_text("🤫 Got it, I'll hang back in groups for you.")


async def chatty_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.set_pref(update.effective_user.id, "personal_mode", "chatty")
    await update.message.reply_text("😄 I'll join in more from now on!")


def _should_reply_in_group(update: Update, bot_username: str) -> bool:
    chat_id = update.effective_chat.id
    settings = db.get_group_settings(chat_id)
    if not settings["groupbot_on"]:
        return False

    text = (update.message.text or "").lower()
    mentioned = f"@{bot_username.lower()}" in text or BOT_NAME.lower() in text
    is_reply_to_bot = (
        update.message.reply_to_message
        and update.message.reply_to_message.from_user
        and update.message.reply_to_message.from_user.username
        and update.message.reply_to_message.from_user.username.lower() == bot_username.lower()
    )
    if mentioned or is_reply_to_bot:
        return True

    prefs = db.get_prefs(update.effective_user.id)
    mode = settings["groupmode"] if settings["groupmode"] != "normal" else prefs["personal_mode"]

    if mode == "quiet":
        chance = 0.03
    elif mode == "chatty":
        chance = 0.25
    else:
        chance = 0.08
    return random.random() < chance


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    if update.message.text.startswith("/"):
        return  # commands are handled elsewhere

    user = update.effective_user
    db.get_or_create_user(user.id, user.username or user.first_name)

    if update.effective_chat.type != "private":
        bot_username = (await context.bot.get_me()).username
        if not _should_reply_in_group(update, bot_username):
            return

    reply = chat_reply(user.id, user.username or user.first_name, update.message.text)
    await update.message.reply_text(reply)

    prefs = db.get_prefs(user.id)
    if prefs["reactions"] and random.random() < 0.3:
        try:
            await update.message.set_reaction(random.choice(REACTION_EMOJIS))
        except Exception:
            pass
