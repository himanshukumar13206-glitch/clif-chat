import random
import time

from telegram import Update
from telegram.ext import ContextTypes

import database as db
from config import DAILY_MIN, DAILY_MAX

DAILY_COOLDOWN = 24 * 60 * 60


def _display_name(u) -> str:
    return u.username and f"@{u.username}" or u.first_name


async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    row = db.get_or_create_user(user.id, user.username or user.first_name)
    rank, total = db.get_rank(user.id)
    rank_text = f"#{rank}/{total}" if rank else "unranked"
    await update.message.reply_text(
        f"💰 Balance: ${row['balance']:,}\n✨ XP: {row['xp']} ({rank_text})"
    )


async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    row = db.get_or_create_user(user.id, user.username or user.first_name)
    now = time.time()
    remaining = DAILY_COOLDOWN - (now - row["last_daily"])
    if remaining > 0:
        hours = int(remaining // 3600)
        mins = int((remaining % 3600) // 60)
        await update.message.reply_text(f"⏳ You've already claimed today. Come back in {hours}h {mins}m.")
        return
    reward = random.randint(DAILY_MIN, DAILY_MAX)
    db.update_balance(user.id, reward)
    db.set_daily_claim(user.id, now)
    db.add_xp(user.id, 10)
    await update.message.reply_text(f"🎁 You claimed your daily reward: +${reward:,}!")


async def give_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to the user you want to send money to: /give <amount>")
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /give <amount> (reply to a user)")
        return
    amount = int(context.args[0])
    if amount <= 0:
        await update.message.reply_text("Amount must be positive.")
        return

    target = update.message.reply_to_message.from_user
    if target.id == user.id:
        await update.message.reply_text("You can't send money to yourself 😅")
        return

    sender = db.get_or_create_user(user.id, user.username or user.first_name)
    if sender["balance"] < amount:
        await update.message.reply_text("You don't have enough balance for that.")
        return

    db.get_or_create_user(target.id, target.username or target.first_name)
    db.update_balance(user.id, -amount)
    db.update_balance(target.id, amount)
    await update.message.reply_text(
        f"💸 {_display_name(user)} sent ${amount:,} to {_display_name(target)}!"
    )


async def toprich_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = db.top_rich(10)
    if not rows:
        await update.message.reply_text("No players yet!")
        return
    lines = ["💰 Richest players 💰"]
    for i, r in enumerate(rows, 1):
        name = f"@{r['username']}" if r["username"] else f"User {r['user_id']}"
        lines.append(f"{i}. {name} — ${r['balance']:,}")
    await update.message.reply_text("\n".join(lines))


async def rank_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    row = db.get_or_create_user(user.id, user.username or user.first_name)
    rank, total = db.get_rank(user.id)
    rank_text = f"#{rank} out of {total}" if rank else "unranked"
    await update.message.reply_text(f"✨ Your rank: {rank_text}\nXP: {row['xp']}")
