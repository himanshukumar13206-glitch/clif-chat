import random
import time

from telegram import Update
from telegram.ext import ContextTypes

import database as db

DAILY_BET_LIMIT = 200
DAY_SECONDS = 24 * 60 * 60


def _parse_bbet_amount(arg: str):
    """Supports plain numbers and the 'X+Y' => X * 10**Y shorthand from bbet."""
    if arg.isdigit():
        return int(arg)
    if "+" in arg:
        left, _, right = arg.partition("+")
        if left.isdigit() and right.isdigit():
            return int(left) * (10 ** int(right))
    return None


def _check_and_bump_daily_limit(user_id: int) -> bool:
    """Returns True if the user is still under today's bet limit."""
    row = db.get_user(user_id)
    now = time.time()
    if now - (row["bet_day"] or 0) > DAY_SECONDS:
        # reset window
        with db.cursor() as cur:
            cur.execute(
                "UPDATE users SET bet_count_today=1, bet_day=? WHERE user_id=?",
                (now, user_id),
            )
        return True

    if row["bet_count_today"] >= DAILY_BET_LIMIT:
        return False

    with db.cursor() as cur:
        cur.execute(
            "UPDATE users SET bet_count_today = bet_count_today + 1 WHERE user_id=?",
            (user_id,),
        )
    return True


async def _run_bet(update: Update, user_id: int, username: str, amount: int):
    row = db.get_or_create_user(user_id, username)

    if amount <= 0:
        await update.message.reply_text("Bet amount must be positive.")
        return
    if row["balance"] < amount:
        await update.message.reply_text("You don't have enough balance for that bet.")
        return
    if not _check_and_bump_daily_limit(user_id):
        await update.message.reply_text(f"🚫 You've hit today's limit of {DAILY_BET_LIMIT} bets. Try again tomorrow!")
        return

    win = random.random() < 0.5
    if win:
        db.update_balance(user_id, amount)
        await update.message.reply_text(f"🎰 You won! +${amount:,} 🎉")
    else:
        db.update_balance(user_id, -amount)
        await update.message.reply_text(f"🎰 You lost ${amount:,}. Better luck next time!")


async def bet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /bet <amount>")
        return
    amount = int(context.args[0])
    await _run_bet(update, user.id, user.username or user.first_name, amount)


async def bbet_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles plain-text 'bbet <amount>' or 'bbet X+Y' messages (no slash)."""
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()
    if not text.lower().startswith("bbet"):
        return
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        await update.message.reply_text("Usage: bbet <amount>  (e.g. bbet 100, or bbet 1+2 for $100)")
        return
    amount = _parse_bbet_amount(parts[1].strip())
    if amount is None:
        await update.message.reply_text("Couldn't parse that bet amount.")
        return
    user = update.effective_user
    await _run_bet(update, user.id, user.username or user.first_name, amount)
