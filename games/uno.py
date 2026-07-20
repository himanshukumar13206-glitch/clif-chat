from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import random

uno_games = {}

async def uno_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    if chat_id in uno_games:
        await update.message.reply_text("UNO game already active.")
        return
    uno_games[chat_id] = {
        "owner": user.id,
        "players": {},
        "stickers": None,   # dict of card -> sticker file_id
        "started": False
    }
    await update.message.reply_text(
        f"🃏 UNO created by {user.mention_html()}!\n"
        "Players can /unojoin. Owner can set stickers with /unostickers (reply to a message with a list of card‑sticker pairs).\n"
        "When ready, use /unostartgame.",
        parse_mode="HTML"
    )

async def uno_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    game = uno_games.get(chat_id)
    if not game:
        await update.message.reply_text("No UNO game. Start with /unostart.")
        return
    if game["started"]:
        await update.message.reply_text("Game already started.")
        return
    if user.id in game["players"]:
        await update.message.reply_text("You already joined.")
        return
    game["players"][user.id] = []   # hand will be stored here
    await update.message.reply_text(f"{user.mention_html()} joined UNO!", parse_mode="HTML")

async def uno_set_stickers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Placeholder: owner can set a mapping of card names to sticker file IDs
    await update.message.reply_text("Sticker setup not fully implemented yet. The owner can manage sticker packs via bot PM.")

# Add more functions: /unostartgame, card play logic, etc.
