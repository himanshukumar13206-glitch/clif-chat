import random
from datetime import datetime
from telegram import Update
from telegram.ext import CallbackContext
from database import (
    get_all_members,
    get_today_festivals,
    get_all_festivals,
    add_member,
    remove_member,
    get_all_members_with_names
)
from keyboards import tag_all_menu, festivals_menu_keyboard

# ---------- ADMIN CHECK ----------
async def is_admin(update: Update, context: CallbackContext) -> bool:
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ('administrator', 'creator')
    except:
        return False

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

def _visible_name(member):
    """Return the best visible name for a member dict."""
    if member.get("first_name"):
        return member["first_name"]
    if member.get("username"):
        return f"@{member['username']}"
    return "User"

async def tag_all(update: Update, context: CallbackContext):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Only admins can use this.")
        return
    args = context.args
    if args:
        custom_msg = " ".join(args)
        context.user_data['tagall_custom'] = custom_msg
    else:
        context.user_data.pop('tagall_custom', None)
    await update.message.reply_text("Choose an option:", reply_markup=tag_all_menu())

async def tag_one_by_one(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    members = get_all_members_with_names(chat_id)
    if not members:
        await query.edit_message_text("No members collected yet. Send any message in the group first!")
        return
    custom = context.user_data.get('tagall_custom', '')
    for m in members:
        name = _visible_name(m)
        mention = f"[{name}](tg://user?id={m['user_id']})"
        text = f"{mention} {custom}".strip()
        try:
            await context.bot.send_message(chat_id, text, parse_mode='Markdown')
        except:
            pass
    await query.edit_message_text("✅ All members tagged one by one.", reply_markup=tag_all_menu())

async def tag_all_in_one(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    members = get_all_members_with_names(chat_id)
    if not members:
        await query.edit_message_text("No members collected yet. Send any message in the group first!")
        return
    custom = context.user_data.get('tagall_custom', '')
    mention_lines = []
    for m in members:
        name = _visible_name(m)
        mention = f"[{name}](tg://user?id={m['user_id']})"
        mention_lines.append(mention)
    mentions = "\n".join(mention_lines)
    text = f"📢 {custom}\n{mentions}" if custom else f"📢 All Members:\n{mentions}"
    try:
        await context.bot.send_message(chat_id, text, parse_mode='Markdown')
    except:
        pass
    await query.edit_message_text("✅ All members tagged in one message.", reply_markup=tag_all_menu())

async def good_morning(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    members = get_all_members_with_names(chat_id)
    if not members:
        await query.edit_message_text("No members to greet.")
        return
    for m in members:
        msg = random.choice(MORNING_MSGS)
        name = _visible_name(m)
        mention = f"[{name}](tg://user?id={m['user_id']})"
        try:
            await context.bot.send_message(chat_id, f"{mention} {msg}", parse_mode='Markdown')
        except:
            pass
    await query.edit_message_text("🌅 Good morning sent to everyone!", reply_markup=tag_all_menu())

async def good_night(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    members = get_all_members_with_names(chat_id)
    if not members:
        await query.edit_message_text("No members to greet.")
        return
    for m in members:
        msg = random.choice(NIGHT_MSGS)
        name = _visible_name(m)
        mention = f"[{name}](tg://user?id={m['user_id']})"
        try:
            await context.bot.send_message(chat_id, f"{mention} {msg}", parse_mode='Markdown')
        except:
            pass
    await query.edit_message_text("🌙 Good night sent to everyone!", reply_markup=tag_all_menu())

# --- FESTIVALS (unchanged) ---
async def festivals_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🎊 Festivals & Events", reply_markup=festivals_menu_keyboard())

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
                await context.bot.send_photo(chat_id=query.message.chat_id, photo=photo_id, caption=caption, parse_mode='Markdown')
            else:
                await context.bot.send_message(query.message.chat_id, caption, parse_mode='Markdown')
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
    if len(text) > 4000:
        text = text[:4000] + "\n...(truncated)"
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=festivals_menu_keyboard())

async def tagall_back(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Choose an option:", reply_markup=tag_all_menu())

# --- MEMBER TRACKING ---
async def new_member(update: Update, context: CallbackContext):
    for member in update.message.new_chat_members:
        add_member(update.effective_chat.id, member.id,
                   first_name=member.first_name or "",
                   username=member.username or "")

async def left_member(update: Update, context: CallbackContext):
    remove_member(update.effective_chat.id, update.message.left_chat_member.id)

async def track_message_sender(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user = update.effective_user
    if chat_id and user and update.effective_chat.type in ('group', 'supergroup'):
        add_member(chat_id, user.id,
                   first_name=user.first_name or "",
                   username=user.username or "")
