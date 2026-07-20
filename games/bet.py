import random
from telegram import Update
from telegram.ext import ContextTypes

# ------------------------------------------------------------
#  Replace these two functions with your real economy logic
# ------------------------------------------------------------
def get_balance(user_id: int) -> int:
    # TODO: replace with your DB call, e.g.:
    # from database import db
    # return db.get_user(user_id)['balance']
    return 1000   # fallback, remove after integration

def update_balance(user_id: int, amount: int):
    # TODO: add/subtract from user's balance in DB
    pass
# ------------------------------------------------------------

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

    balance = get_balance(user.id)
    if wager > balance:
        await update.message.reply_text(f"You only have {balance} coins.")
        return

    # 50% chance to win
    if random.random() < 0.5:
        winnings = wager  # double or nothing → get back wager *2
        update_balance(user.id, winnings)
        await update.message.reply_text(
            f"🎉 You won! +{winnings} coins.\nNew balance: {get_balance(user.id)}"
        )
    else:
        update_balance(user.id, -wager)
        await update.message.reply_text(
            f"💸 You lost {wager} coins.\nNew balance: {get_balance(user.id)}"
        )

async def bbet_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Triggered when a message starts with 'bbet <amount>' (case‑insensitive)."""
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

    # call the same logic as /bet but using wager
    user = update.effective_user
    balance = get_balance(user.id)
    if wager <= 0 or wager > balance:
        await update.message.reply_text(f"You only have {balance} coins.")
        return

    if random.random() < 0.5:
        update_balance(user.id, wager)
        await update.message.reply_text(f"🎉 bbet won! +{wager} coins.")
    else:
        update_balance(user.id, -wager)
        await update.message.reply_text(f"💸 bbet lost {wager} coins.")
