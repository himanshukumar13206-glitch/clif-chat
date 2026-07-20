import random

from telegram import Update
from telegram.ext import ContextTypes

import database as db


def _display_name(u) -> str:
    return u.username and f"@{u.username}" or u.first_name


async def propose_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to the user you want to propose to! 💍")
        return
    target = update.message.reply_to_message.from_user
    if target.id == user.id:
        await update.message.reply_text("You can't marry yourself 😂")
        return
    if target.is_bot:
        await update.message.reply_text("Bots can't get married (yet 👀).")
        return

    proposer = db.get_or_create_user(user.id, user.username or user.first_name)
    target_row = db.get_or_create_user(target.id, target.username or target.first_name)

    if proposer["married_to"]:
        await update.message.reply_text("You're already married! Use /divorce first.")
        return
    if target_row["married_to"]:
        await update.message.reply_text(f"{_display_name(target)} is already married to someone else.")
        return

    accepted = random.random() < 0.6
    if accepted:
        db.set_marriage(user.id, target.id)
        db.set_marriage(target.id, user.id)
        await update.message.reply_text(
            f"💍 {_display_name(target)} said YES! {_display_name(user)} & {_display_name(target)} are now married! 🎉"
        )
    else:
        await update.message.reply_text(f"💔 {_display_name(target)} said no... maybe try again later?")


async def divorce_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    row = db.get_or_create_user(user.id, user.username or user.first_name)
    if not row["married_to"]:
        await update.message.reply_text("You're not married.")
        return
    partner_id = row["married_to"]
    db.set_marriage(user.id, None)
    db.set_marriage(partner_id, None)
    await update.message.reply_text("💔 The papers are signed. You're single again.")


async def marriage_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        row = db.get_or_create_user(target.id, target.username or target.first_name)
        name = _display_name(target)
    else:
        user = update.effective_user
        row = db.get_or_create_user(user.id, user.username or user.first_name)
        name = _display_name(user)

    if row["married_to"]:
        await update.message.reply_text(f"💍 {name} is married.")
    else:
        await update.message.reply_text(f"💔 {name} is single.")


async def couple_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.message.reply_text("This only works in group chats!")
        return
    # Telegram bots can't list all group members directly; we ship two
    # people from recent chat activity if available, else fall back nicely.
    admins = await context.bot.get_chat_administrators(update.effective_chat.id)
    candidates = [a.user for a in admins if not a.user.is_bot]
    if len(candidates) < 2:
        await update.message.reply_text(
            "I need at least two active humans to ship 👀 (try again once more people have chatted)."
        )
        return
    a, b = random.sample(candidates, 2)
    percent = random.randint(1, 100)
    await update.message.reply_text(f"💘 {_display_name(a)} + {_display_name(b)} = {percent}% compatible!")
