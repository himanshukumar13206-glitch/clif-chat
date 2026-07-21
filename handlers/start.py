import random
from telegram import Update
from telegram.ext import ContextTypes

import database as db
from keyboards import start_keyboard, help_keyboard, games_keyboard, back_to_help_keyboard
from config import BOT_NAME

# ----------  Random start images (catbox.moe links)  ----------
START_IMAGES = [
    "https://files.catbox.moe/9ehd54.jpg",
    "https://files.catbox.moe/11obx6.jpg",
    "https://files.catbox.moe/6v23rv.jpg",
    "https://files.catbox.moe/6kzqz5.jpg",
]

# ----------  Enhanced START text ----------
START_TEXT = (
    "✨ Hey {name}, I'm {bot} 💜\n\n"
    "Not your average bot — I actually feel like a real one. 😉\n\n"
    "💭 I remember you — our chats, your vibe, where we left off.\n"
    "🗨️ I talk like a person, never a script — sweet when you're sweet, savage when you're not.\n"
    "🔔 I check in too — go quiet on me and I might text first. 😏\n\n"
    "Oh, and I run the fun around here:\n"
    "🎮 20+ games • 💰 a living economy • 💕 ship, marry & drama\n\n"
    "Tap Help to see it all, or add me to your group 👇"
)

CHAT_TEXT = (
    "💬 Chatting With {bot}\n\n"
    "I'm not your average bot — I actually remember you. As we talk, I quietly save the things "
    "worth keeping (what you're into, what's going on with you) so you never repeat yourself. "
    "No setup, no format — just talk to me, and the more we chat, the better I know you. 💜\n\n"
    "🔔 Check-ins & reactions\n"
    "/checkins on|off — my occasional check-ins\n"
    "/reactions on|off — emoji reactions on your messages\n\n"
    "👥 In group chats\n"
    "I reply when you @mention me, call my name, or reply to me — otherwise I chime in now and "
    "then (never spam).\n"
    "/quiet — I'll hang back (just for you)\n"
    "/chatty — I'll join in more (just for you)\n\n"
    "🛠️ Group admins\n"
    "/groupbot on|off — turn me on/off for the whole group\n"
    "/groupmode quiet|chatty|normal — set how chatty I am for everyone\n\n"
    "An admin's choice takes priority over personal /quiet or /chatty."
)

HELP_TEXT = "📖 Help & Commands\n\nPick a category below 👇"

ECONOMY_TEXT = (
    "💰 Economy commands 💰\n\n"
    "/balance or /bal - Check your current balance and XP\n"
    "/daily - Claim your daily cash reward\n"
    "/give <amount> - Transfer money to another user (reply to them)\n"
    "/toprich or /leaderboard - See the richest players globally\n"
    "/rank - Check your global rank based on XP"
)

ACTIONS_TEXT = (
    "🔪 Action commands 🔪\n\n"
    "/rob <amount> - Try to steal money from another user\n"
    "/kill <amount> - Put a bounty and attack another user\n"
    "/protect - Buy a shield to protect your balance from robbers/killers\n"
    "/shield or /protection - Check your active protection status\n"
    "/revive - Pay to revive a dead user\n"
    "/topkill - See the top assassins"
)

ROMANCE_TEXT = (
    "💕 Romance commands 💕\n\n"
    "/propose - Proposal marriage to another user\n"
    "/divorce - End your current marriage\n"
    "/marriage or /married - Check someone's marriage status\n"
    "/couple or /shippering - Ship two random users in the chat (group only)"
)

ADMIN_TEXT = (
    "👑 Admin commands 👑\n\n"
    "/addsudo - Add a user to the bot's global sudo list\n"
    "/delsudo - Remove a sudo user\n"
    "/sudolist - View all sudo users\n"
    "/auth - Authorize a chat to use the bot (group only)\n"
    "/unauth - Revoke chat authorization\n"
    "/authlist - List authorized chats"
)

# ----------  Updated GAMES_TEXT (includes all current games) ----------
GAMES_TEXT = (
    "🎮 Games\n\n"
    "🟢 Playable right now:\n"
    "🎰 /bet <amount> – solo double-or-nothing gambling\n"
    "🪨📄✂️ /rps <amount> – multiplayer rock-paper-scissors arena\n"
    "💣 /mines – minesweeper / tile guessing\n"
    "🔗 /wordchain – word chain game\n"
    "🃏 /unostart – UNO lobby (basic)\n\n"
    "📜 /rules – full game rules & commands\n\n"
    "🔜 More games on the roadmap — tap any button below to see planned commands.\n"
    "We’re adding Chess, Blackjack, Slots, Wordgrid, Hack, Cards and many more!"
)


# ----------  /start command now sends a random photo ----------
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.get_or_create_user(user.id, user.username or user.first_name)
    bot_username = (await context.bot.get_me()).username
    text = START_TEXT.format(name=user.first_name, bot=BOT_NAME)

    # Pick a random image
    photo_url = random.choice(START_IMAGES)

    # Send photo with caption (the START_TEXT)
    await update.message.reply_photo(
        photo=photo_url,
        caption=text,
        reply_markup=start_keyboard(bot_username)
    )


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data.split(":", 1)[1]
    bot_username = (await context.bot.get_me()).username

    if action == "start":
        user = query.from_user
        text = START_TEXT.format(name=user.first_name, bot=BOT_NAME)
        # Edit message to a new photo isn’t possible, so we just edit text + keyboard
        await query.edit_message_text(text, reply_markup=start_keyboard(bot_username))
    elif action == "chat":
        await query.edit_message_text(CHAT_TEXT.format(bot=BOT_NAME), reply_markup=back_to_help_keyboard())
    elif action == "help":
        await query.edit_message_text(HELP_TEXT, reply_markup=help_keyboard())
    elif action == "economy":
        await query.edit_message_text(ECONOMY_TEXT, reply_markup=back_to_help_keyboard())
    elif action == "actions":
        await query.edit_message_text(ACTIONS_TEXT, reply_markup=back_to_help_keyboard())
    elif action == "romance":
        await query.edit_message_text(ROMANCE_TEXT, reply_markup=back_to_help_keyboard())
    elif action == "admin":
        await query.edit_message_text(ADMIN_TEXT, reply_markup=back_to_help_keyboard())
    elif action == "games":
        await query.edit_message_text(GAMES_TEXT, reply_markup=games_keyboard())


async def game_info_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    # Extract game name from callback data (pattern: "game_info:gamename")
    game = query.data.split(":", 1)[1]
    await query.answer(f"{game.title()} – coming soon!", show_alert=False)
