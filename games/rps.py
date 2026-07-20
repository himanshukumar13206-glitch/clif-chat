import random

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

import database as db

# In-memory lobby state: { chat_id: {"amount": int, "players": {user_id: username}, "host": user_id, "started": bool} }
_lobbies = {}

CHOICES = ["rock", "paper", "scissors"]
BEATS = {"rock": "scissors", "paper": "rock", "scissors": "paper"}


def _choice_keyboard(chat_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🪨", callback_data=f"rps_choice:{chat_id}:rock"),
         InlineKeyboardButton("📄", callback_data=f"rps_choice:{chat_id}:paper"),
         InlineKeyboardButton("✂️", callback_data=f"rps_choice:{chat_id}:scissors")]
    ])


async def rps_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if update.effective_chat.type == "private":
        await update.message.reply_text("RPS lobbies only work in group chats!")
        return
    if chat_id in _lobbies:
        await update.message.reply_text("A game is already active here. Use /end to stop it.")
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /rps <amount>")
        return
    amount = int(context.args[0])
    user = update.effective_user
    row = db.get_or_create_user(user.id, user.username or user.first_name)
    if row["balance"] < amount:
        await update.message.reply_text("You don't have enough balance to start that bet.")
        return

    _lobbies[chat_id] = {
        "amount": amount,
        "players": {user.id: user.username or user.first_name},
        "host": user.id,
        "started": False,
        "choices": {},
    }
    await update.message.reply_text(
        f"🪨📄✂️ RPS lobby started by {user.first_name} for ${amount:,}!\n"
        f"Use /joinrps to join (2-5 players). Host can /end to cancel."
    )


async def joinrps_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    lobby = _lobbies.get(chat_id)
    if not lobby or lobby["started"]:
        await update.message.reply_text("No open RPS lobby to join right now.")
        return
    user = update.effective_user
    if user.id in lobby["players"]:
        await update.message.reply_text("You're already in!")
        return
    if len(lobby["players"]) >= 5:
        await update.message.reply_text("Lobby is full (5 players max).")
        return
    row = db.get_or_create_user(user.id, user.username or user.first_name)
    if row["balance"] < lobby["amount"]:
        await update.message.reply_text("You don't have enough balance to join this bet.")
        return

    lobby["players"][user.id] = user.username or user.first_name
    await update.message.reply_text(f"✅ {user.first_name} joined! ({len(lobby['players'])}/5)")

    if len(lobby["players"]) >= 2:
        await _start_round(update, context, chat_id)


async def _start_round(update, context, chat_id):
    lobby = _lobbies[chat_id]
    lobby["started"] = True
    lobby["choices"] = {}
    for uid in lobby["players"]:
        try:
            await context.bot.send_message(
                uid, f"🪨📄✂️ Pick your move for the ${lobby['amount']:,} RPS game!",
                reply_markup=_choice_keyboard(chat_id),
            )
        except Exception:
            pass
    await update.message.reply_text("🎮 Round started! Check your DMs to pick rock, paper, or scissors.")


async def rps_choice_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, chat_id_str, choice = query.data.split(":")
    chat_id = int(chat_id_str)
    lobby = _lobbies.get(chat_id)
    if not lobby or not lobby["started"]:
        await query.edit_message_text("This game has ended.")
        return
    user = query.from_user
    if user.id not in lobby["players"]:
        await query.edit_message_text("You're not part of this game.")
        return

    lobby["choices"][user.id] = choice
    await query.edit_message_text(f"You picked {choice}. Waiting for others...")

    if len(lobby["choices"]) == len(lobby["players"]):
        await _resolve_round(context, chat_id)


async def _resolve_round(context, chat_id):
    lobby = _lobbies.pop(chat_id, None)
    if not lobby:
        return
    choices = lobby["choices"]
    amount = lobby["amount"]

    picks = set(choices.values())
    result_lines = [f"{lobby['players'][uid]}: {c}" for uid, c in choices.items()]

    if len(picks) == 1:
        outcome = "🤝 Everyone picked the same thing — it's a draw, no money changes hands."
        winners = []
    elif len(picks) == 3:
        outcome = "🤯 Rock, paper AND scissors all appeared — total draw, no money changes hands!"
        winners = []
    else:
        # exactly two distinct choices among 2-5 players
        a, b = tuple(picks)
        winning_choice = a if BEATS[a] == b else b
        winners = [uid for uid, c in choices.items() if c == winning_choice]
        losers = [uid for uid in choices if uid not in winners]
        pot_per_loser = amount
        total_pot = pot_per_loser * len(losers)
        share = total_pot // len(winners) if winners else 0
        for uid in losers:
            db.update_balance(uid, -pot_per_loser)
        for uid in winners:
            db.update_balance(uid, share)
        names = ", ".join(lobby["players"][uid] for uid in winners)
        outcome = f"🏆 {winning_choice} wins! {names} each gain ${share:,}!"

    await context.bot.send_message(
        chat_id,
        "🪨📄✂️ Results:\n" + "\n".join(result_lines) + "\n\n" + outcome,
    )


async def end_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in _lobbies:
        del _lobbies[chat_id]
        await update.message.reply_text("🛑 Game ended.")
    else:
        await update.message.reply_text("No active game to end.")
