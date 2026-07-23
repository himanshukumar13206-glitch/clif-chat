import random
from datetime import datetime
from telegram import Update, ParseMode
from telegram.ext import CallbackContext
from database import (
    get_all_members,
    get_today_festivals,
    get_all_festivals,
    add_member,
    remove_member
)
from keyboard import tag_all_menu, festivals_menu_keyboard

# ---------- ADMIN CHECK ----------
def is_admin(update: Update, context: CallbackContext) -> bool:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    try:
        member = context.bot.get_chat_member(chat_id, user_id)
        return member.status in ('administrator', 'creator')
    except:
        return False

# ---------- GOOD MORNING MESSAGES ----------
MORNING_MSGS = [
    "🌞 Good Morning, rise and shine!",
    "राधे राधे ☀️ सुप्रभात!",
    "Good Morning! Have a blessed day.",
    "उठो सूरज की पहली किरण के साथ, जय श्री राम 🌄",
    "Morning! Let's make today awesome.",
    "प्रभात का आनंद लो, हरि ॐ 🌺",
    "Rise and grind! Good Morning 🌻",
    "जय माता दी, सुप्रभात! 🌼"
]

NIGHT_MSGS = [
    "🌙 Good Night, sleep tight!",
    "शुभ रात्रि, मीठे सपने देखो 🌜",
    "Good Night! Tomorrow will be better.",
    "राम राम, शुभ रात्रि 🌛",
    "Good Night! Stars are shining for you.",
    "शुभ रात्रि, कल फिर मिलेंगे ✨"
]

# ---------- TAG ALL FUNCTIONS ----------
async def tag_all(update: Update, context: CallbackContext):
    """Entry point for /tagall command"""
    if not is_admin(update, context):
        await update.message.reply_text("❌ Only admins can use this.")
        return
    await update.message.reply_text(
        "Choose an option:",
        reply_markup=tag_all_menu()
    )

async def tag_one_by_one(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    members = get_all_members(chat_id)
    if not members:
        await query.edit_message_text("No members in database yet.")
        return
    for uid in members:
        try:
            await context.bot.send_message(
                chat_id,
                f"[User](tg://user?id={uid})",
                parse_mode=ParseMode.MARKDOWN
            )
        except:
            pass
    await query.edit_message_text("✅ All members tagged one by one.", reply_markup=tag_all_menu())

async def tag_all_in_one(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    members = get_all_members(chat_id)
    if not members:
        await query.edit_message_text("No members found.")
        return
    mentions = " ".join([f"[⁠](tg://user?id={uid})" for uid in members])  # invisible mention trick
    await context.bot.send_message(
        chat_id,
        f"📢 All Members: {mentions}",
        parse_mode=ParseMode.MARKDOWN
    )
    await query.edit_message_text("✅ All members tagged in one message.", reply_markup=tag_all_menu())

async def good_morning(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    members = get_all_members(chat_id)
    if not members:
        await query.edit_message_text("No members to greet.")
        return
    for uid in members:
        msg = random.choice(MORNING_MSGS)
        try:
            await context.bot.send_message(
                chat_id,
                f"[User](tg://user?id={uid}) {msg}",
                parse_mode=ParseMode.MARKDOWN
            )
        except:
            pass
    await query.edit_message_text("🌅 Good morning sent to everyone!", reply_markup=tag_all_menu())

async def good_night(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    members = get_all_members(chat_id)
    if not members:
        await query.edit_message_text("No members to greet.")
        return
    for uid in members:
        msg = random.choice(NIGHT_MSGS)
        try:
            await context.bot.send_message(
                chat_id,
                f"[User](tg://user?id={uid}) {msg}",
                parse_mode=ParseMode.MARKDOWN
            )
        except:
            pass
    await query.edit_message_text("🌙 Good night sent to everyone!", reply_markup=tag_all_menu())

# ---------- FESTIVALS & EVENTS ----------
async def festivals_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🎊 Festivals & Events",
        reply_markup=festivals_menu_keyboard()
    )

async def today_festival(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    today = datetime.now()
    festivals = get_today_festivals(today.month, today.day)
    if not festivals:
        await query.edit_message_text("📭 No festival/event today.", reply_markup=festivals_menu_keyboard())
        return
    for name, meaning, photo_id in festivals:
        caption = f"🎉 *{name}*\n\n_{meaning}_"
        try:
            if photo_id:
                await context.bot.send_photo(
                    chat_id=query.message.chat_id,
                    photo=photo_id,
                    caption=caption,
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await context.bot.send_message(
                    query.message.chat_id,
                    caption,
                    parse_mode=ParseMode.MARKDOWN
                )
        except:
            pass
    await query.edit_message_text("✅ Today's events/festivals shown above.", reply_markup=festivals_menu_keyboard())

async def all_festivals(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    festivals = get_all_festivals()
    if not festivals:
        await query.edit_message_text("No festivals stored.", reply_markup=festivals_menu_keyboard())
        return
    text = "📜 *All Festivals*\n\n"
    for name, meaning, photo_id, month, day in festivals:
        text += f"🗓 {day}/{month} - *{name}*: _{meaning}_\n"
    # Splitting if too long
    if len(text) > 4000:
        text = text[:4000] + "\n...(truncated)"
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=festivals_menu_keyboard())

async def tagall_back(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Choose an option:", reply_markup=tag_all_menu())

# ---------- MEMBER TRACKING ----------
async def new_member(update: Update, context: CallbackContext):
    for member in update.message.new_chat_members:
        add_member(update.effective_chat.id, member.id)

async def left_member(update: Update, context: CallbackContext):
    remove_member(update.effective_chat.id, update.message.left_chat_member.id)
