import random
from telegram import Update
from telegram.ext import ContextTypes
import database as db          # <-- FIXED: import module as alias

async def bet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not context.args:
        await update.message.reply_text("Usage: /bet <amount>")
        return
    try:
        wager = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Please enter a valid number.")
        return
    if wager <= 0:
        await update.message.reply_text("Bet a positive amount!")
        return

    user_data = db.get_user(user.id)          # now works
    balance = user_data["balance"] if user_data else 0
    if wager > balance:
        await update.message.reply_text(f"You only have {balance} coins.")
        return

    if random.random() < 0.5:
        db.update_balance(user.id, wager)     # add winnings
        new_bal = db.get_user(user.id)["balance"]
        await update.message.reply_text(f"🎉 You won! +{wager} coins.\nNew balance: {new_bal}")
    else:
        db.update_balance(user.id, -wager)
        new_bal = db.get_user(user.id)["balance"]
        await update.message.reply_text(f"💸 You lost {wager} coins.\nNew balance: {new_bal}")

async def bbet_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Triggered by messages starting with 'bbet <amount>' (case insensitive)."""
    text = update.message.text.strip()
    parts = text.split()
    if len(parts) != 2:
        await update.message.reply_text("Usage: bbet <amount>")
        return
    try:
        wager = int(parts[1])
    except ValueError:
        await update.message.reply_text("Invalid amount.")
        return
    user = update.effective_user
    user_data = db.get_user(user.id)
    balance = user_data["balance"] if user_data else 0
    if wager <= 0 or wager > balance:
        await update.message.reply_text(f"You only have {balance} coins.")
        return

    if random.random() < 0.5:
        db.update_balance(user.id, wager)
        await update.message.reply_text(f"🎉 bbet won! +{wager} coins.")
    else:
        db.update_balance(user.id, -wager)
        await update.message.reply_text(f"💸 bbet lost {wager} coins.")
