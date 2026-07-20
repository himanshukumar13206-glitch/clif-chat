from telegram import Update
from telegram.ext import ContextTypes

import database as db
from config import OWNER_ID


def _is_owner_or_sudo(user_id: int) -> bool:
    return user_id == OWNER_ID or db.is_sudo(user_id)


async def _is_group_admin(update: Update) -> bool:
    if update.effective_chat.type == "private":
        return False
    member = await update.effective_chat.get_member(update.effective_user.id)
    return member.status in ("administrator", "creator")


async def addsudo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_owner_or_sudo(update.effective_user.id) and update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Only the bot owner can do that.")
        return
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Only the bot owner can add sudo users.")
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to the user you want to add as sudo.")
        return
    target = update.message.reply_to_message.from_user
    db.add_sudo(target.id)
    await update.message.reply_text(f"✅ Added {target.first_name} to sudo list.")


async def delsudo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Only the bot owner can remove sudo users.")
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to the user you want to remove from sudo.")
        return
    target = update.message.reply_to_message.from_user
    db.del_sudo(target.id)
    await update.message.reply_text(f"✅ Removed {target.first_name} from sudo list.")


async def sudolist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ids = db.list_sudo()
    if not ids:
        await update.message.reply_text("No sudo users yet.")
        return
    await update.message.reply_text("👑 Sudo users:\n" + "\n".join(str(i) for i in ids))


async def auth_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.message.reply_text("This command is for groups only.")
        return
    if not (_is_owner_or_sudo(update.effective_user.id)):
        await update.message.reply_text("Only sudo users can authorize chats.")
        return
    db.add_auth_chat(update.effective_chat.id)
    await update.message.reply_text("✅ This chat is now authorized to use the bot.")


async def unauth_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not (_is_owner_or_sudo(update.effective_user.id)):
        await update.message.reply_text("Only sudo users can revoke authorization.")
        return
    db.del_auth_chat(update.effective_chat.id)
    await update.message.reply_text("🚫 This chat's authorization has been revoked.")


async def authlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ids = db.list_auth_chats()
    if not ids:
        await update.message.reply_text("No authorized chats yet.")
        return
    await update.message.reply_text("📋 Authorized chats:\n" + "\n".join(str(i) for i in ids))


# ---------- Group settings (groupbot / groupmode) ----------

async def groupbot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.message.reply_text("This only works in groups.")
        return
    if not await _is_group_admin(update):
        await update.message.reply_text("Only group admins can use this.")
        return
    if not context.args or context.args[0].lower() not in ("on", "off"):
        await update.message.reply_text("Usage: /groupbot on|off")
        return
    on = context.args[0].lower() == "on"
    db.set_groupbot(update.effective_chat.id, on)
    await update.message.reply_text(f"🛠️ Group bot is now {'ON' if on else 'OFF'}.")


async def groupmode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.message.reply_text("This only works in groups.")
        return
    if not await _is_group_admin(update):
        await update.message.reply_text("Only group admins can use this.")
        return
    if not context.args or context.args[0].lower() not in ("quiet", "chatty", "normal"):
        await update.message.reply_text("Usage: /groupmode quiet|chatty|normal")
        return
    mode = context.args[0].lower()
    db.set_groupmode(update.effective_chat.id, mode)
    await update.message.reply_text(f"🛠️ Group chat mode set to {mode}.")
