import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import database as db   # <-- import whole module

active_games = {}   # {chat_id: {"host": user_id, "wager": int, "players": {user_id: choice}}}

async def rps_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    if chat_id in active_games:
        await update.message.reply_text("An RPS game is already running here.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /rps <wager>")
        return
    try:
        wager = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid wager.")
        return
    if wager <= 0:
        await update.message.reply_text("Wager must be positive.")
        return

    user_data = db.get_user(user.id)
    if not user_data or user_data["balance"] < wager:
        await update.message.reply_text("You don't have enough coins.")
        return

    # Deduct the host's wager up front so it can't be spent elsewhere
    db.update_balance(user.id, -wager)

    active_games[chat_id] = {
        "host": user.id,
        "wager": wager,
        "players": {user.id: None}   # host auto-joins
    }
    keyboard = [[InlineKeyboardButton("Join Game", callback_data="rps_join")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"🪨📄✂️ RPS arena created by {user.mention_html()}!\n"
        f"Wager: {wager} coins. Tap below to join.\n"
        f"When 2+ players have joined, the host can type /end to start the match.",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

async def joinrps_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    game = active_games.get(chat_id)
    if not game:
        await update.message.reply_text("No active RPS game. Start one with /rps.")
        return
    if user.id in game["players"]:
        await update.message.reply_text("You already joined.")
        return
    user_data = db.get_user(user.id)
    if not user_data or user_data["balance"] < game["wager"]:
        await update.message.reply_text("You don't have enough coins to join.")
        return

    # Deduct the wager at join time so it's actually at stake
    db.update_balance(user.id, -game["wager"])

    game["players"][user.id] = None
    await update.message.reply_text(f"{user.mention_html()} joined the arena!", parse_mode="HTML")

async def end_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    game = active_games.get(chat_id)
    if not game:
        await update.message.reply_text("No RPS game running.")
        return
    if user.id != game["host"]:
        await update.message.reply_text("Only the host can start the match.")
        return
    if len(game["players"]) < 2:
        await update.message.reply_text("Need at least 2 players.")
        return

    for player_id in game["players"]:
        try:
            await context.bot.send_message(
                player_id,
                "Choose your move:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🪨 Rock", callback_data=f"rps_choice:{player_id}:rock"),
                     InlineKeyboardButton("📄 Paper", callback_data=f"rps_choice:{player_id}:paper"),
                     InlineKeyboardButton("✂️ Scissors", callback_data=f"rps_choice:{player_id}:scissors")]
                ])
            )
        except Exception:
            await update.message.reply_text(f"Could not message player {player_id}. They need to start the bot first.")
            return
    await update.message.reply_text("Match started! Check your DMs to choose your move.")

async def rps_choice_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split(":")
    if len(data) != 3:
        return
    player_id = int(data[1])
    choice = data[2]

    # Find game
    chat_id = None
    for cid, game in active_games.items():
        if player_id in game["players"]:
            chat_id = cid
            break
    if chat_id is None:
        await query.edit_message_text("No active game found.")
        return

    game = active_games[chat_id]
    if game["players"][player_id] is not None:
        await query.edit_message_text("You already chose!")
        return

    game["players"][player_id] = choice
    await query.edit_message_text(f"You chose {choice}.")

    # Check if all players chose
    if all(v is not None for v in game["players"].values()):
        players = list(game["players"].items())
        if len(players) != 2:
            await context.bot.send_message(chat_id, "Only 2‑player RPS is implemented for now.")
            del active_games[chat_id]
            return

        p1_id, p1 = players[0]
        p2_id, p2 = players[1]
        beats = {"rock": "scissors", "paper": "rock", "scissors": "paper"}
        wager = game["wager"]
        if p1 == p2:
            result = "It's a draw!"
            # Return wagers (they were deducted at join time)
            db.update_balance(p1_id, wager)
            db.update_balance(p2_id, wager)
        elif beats[p1] == p2:
            result = f"Player {p1_id} wins!"
            db.update_balance(p1_id, wager * 2)   # they get both wagers back
        else:
            result = f"Player {p2_id} wins!"
            db.update_balance(p2_id, wager * 2)

        await context.bot.send_message(chat_id, f"RPS result: {result}")
        del active_games[chat_id]
