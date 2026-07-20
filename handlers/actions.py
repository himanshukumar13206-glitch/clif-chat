import random
import time

from telegram import Update
from telegram.ext import ContextTypes

import database as db
from config import PROTECT_COST, PROTECT_HOURS, REVIVE_COST


def _display_name(u) -> str:
    return u.username and f"@{u.username}" or u.first_name


def _require_reply_and_amount(update):
    if not update.message.reply_to_message:
        return None, None, "Reply to the user you want to target."
    if not update.message.text.split():
        return None, None, "Usage: /rob <amount>"
    parts = update.message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        return None, None, "Usage: /rob <amount>"
    return update.message.reply_to_message.from_user, int(parts[1]), None


async def rob_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    target, amount, err = _require_reply_and_amount(update)
    if err:
        await update.message.reply_text(err)
        return
    if target.id == user.id:
        await update.message.reply_text("You can't rob yourself 😂")
        return

    robber = db.get_or_create_user(user.id, user.username or user.first_name)
    victim = db.get_or_create_user(target.id, target.username or target.first_name)

    if db.is_protected(target.id):
        await update.message.reply_text(f"🛡️ {_display_name(target)} is shielded — the robbery failed!")
        return
    if victim["balance"] < amount:
        await update.message.reply_text(f"{_display_name(target)} doesn't even have that much 💀")
        return

    success = random.random() < 0.45
    if success:
        db.update_balance(target.id, -amount)
        db.update_balance(user.id, amount)
        await update.message.reply_text(
            f"🔪 {_display_name(user)} successfully robbed ${amount:,} from {_display_name(target)}!"
        )
    else:
        fine = min(robber["balance"], amount // 2)
        db.update_balance(user.id, -fine)
        await update.message.reply_text(
            f"🚨 {_display_name(user)} got caught robbing {_display_name(target)} and paid a ${fine:,} fine!"
        )


async def kill_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    target, amount, err = _require_reply_and_amount(update)
    if err:
        await update.message.reply_text(err)
        return
    if target.id == user.id:
        await update.message.reply_text("You can't put a bounty on yourself 💀")
        return

    killer = db.get_or_create_user(user.id, user.username or user.first_name)
    db.get_or_create_user(target.id, target.username or target.first_name)

    if killer["balance"] < amount:
        await update.message.reply_text("You don't have enough for that bounty.")
        return

    if db.is_protected(target.id):
        await update.message.reply_text(f"🛡️ {_display_name(target)} is shielded — the attack failed!")
        return

    db.update_balance(user.id, -amount)
    success = random.random() < 0.5
    if success:
        db.set_alive(target.id, False)
        db.increment_kills(user.id)
        db.update_balance(user.id, amount * 2)
        await update.message.reply_text(
            f"☠️ {_display_name(user)} took out {_display_name(target)}! (+${amount * 2:,})\n"
            f"{_display_name(target)} can /revive to come back."
        )
    else:
        await update.message.reply_text(
            f"💨 The hit on {_display_name(target)} failed. {_display_name(user)} lost ${amount:,}."
        )


async def protect_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    row = db.get_or_create_user(user.id, user.username or user.first_name)
    if row["balance"] < PROTECT_COST:
        await update.message.reply_text(f"You need ${PROTECT_COST:,} to buy protection.")
        return
    db.update_balance(user.id, -PROTECT_COST)
    until = time.time() + PROTECT_HOURS * 3600
    db.set_protection(user.id, until)
    await update.message.reply_text(f"🛡️ You're protected for the next {PROTECT_HOURS} hours!")


async def shield_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    row = db.get_or_create_user(user.id, user.username or user.first_name)
    remaining = row["protected_until"] - time.time()
    if remaining > 0:
        hours = int(remaining // 3600)
        mins = int((remaining % 3600) // 60)
        await update.message.reply_text(f"🛡️ Protection active for {hours}h {mins}m.")
    else:
        await update.message.reply_text("No active protection. Use /protect to buy some.")


async def revive_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    row = db.get_or_create_user(user.id, user.username or user.first_name)
    if row["alive"]:
        await update.message.reply_text("You're already alive!")
        return
    if row["balance"] < REVIVE_COST:
        await update.message.reply_text(f"You need ${REVIVE_COST:,} to revive.")
        return
    db.update_balance(user.id, -REVIVE_COST)
    db.set_alive(user.id, True)
    await update.message.reply_text("💫 You're back among the living!")


async def topkill_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = db.top_killers(10)
    if not rows:
        await update.message.reply_text("No assassins yet!")
        return
    lines = ["🔪 Top assassins 🔪"]
    for i, r in enumerate(rows, 1):
        name = f"@{r['username']}" if r["username"] else f"User {r['user_id']}"
        lines.append(f"{i}. {name} — {r['kills']} kills")
    await update.message.reply_text("\n".join(lines))
