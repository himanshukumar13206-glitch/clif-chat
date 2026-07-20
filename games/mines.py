import random
from telegram import Update
from telegram.ext import ContextTypes
import database as db          # <-- fixed import

games = {}   # {chat_id: {"bombs": set, "revealed": set, "score": 0, "grid": 5}}

async def mines_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in games:
        await update.message.reply_text("A Mines game is already running here. Finish it first!")
        return
    # 5x5 grid, 3 bombs
    bombs = set(random.sample(range(25), 3))
    games[chat_id] = {"bombs": bombs, "revealed": set(), "score": 0, "grid": 5}
    await update.message.reply_text(
        "💣 Mines started! Send numbers 1‑25 to reveal a tile.\n"
        "10 points per safe tile. Hit a bomb = game over.\n"
        "Type /stopmines to quit."
    )

async def mines_tile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    game = games.get(chat_id)
    if not game:
        return
    text = update.message.text.strip()
    if not text.isdigit():
        return
    tile = int(text)
    if tile < 1 or tile > 25:
        await update.message.reply_text("Pick a number between 1 and 25.")
        return
    idx = tile - 1
    if idx in game["revealed"]:
        await update.message.reply_text("Already revealed.")
        return
    game["revealed"].add(idx)
    if idx in game["bombs"]:
        await update.message.reply_text(f"💥 Bomb! Game over. Score: {game['score']}")
        del games[chat_id]
    else:
        game["score"] += 10
        safe_left = 25 - len(game["revealed"])
        bomb_left = 3 - len(game["revealed"] & game["bombs"])
        await update.message.reply_text(f"✅ Safe! +10. Score: {game['score']}. Safe left: {safe_left}, Bombs left: {bomb_left}")
        if safe_left == len(game["bombs"]):
            await update.message.reply_text(f"🎉 You cleared the board! Final score: {game['score']}")   # fixed line
            del games[chat_id]

async def stop_mines(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in games:
        del games[chat_id]
        await update.message.reply_text("Mines game stopped.")
    else:
        await update.message.reply_text("No active Mines game.")
