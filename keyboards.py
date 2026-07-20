from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def start_keyboard(bot_username: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Chat with me", callback_data="menu:chat")],
        [InlineKeyboardButton("📖 Help & Commands", callback_data="menu:help")],
        [InlineKeyboardButton("📢 Updates", url="https://t.me/")],
        [InlineKeyboardButton("🛟 Support", url="https://t.me/")],
        [InlineKeyboardButton("➕ Add me to your group",
                               url=f"https://t.me/{bot_username}?startgroup=true")],
    ])


def help_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Chat with me", callback_data="menu:chat")],
        [InlineKeyboardButton("💰 Economy", callback_data="menu:economy"),
         InlineKeyboardButton("🔪 Actions", callback_data="menu:actions")],
        [InlineKeyboardButton("💕 Romance", callback_data="menu:romance"),
         InlineKeyboardButton("🎮 Games", callback_data="menu:games")],
        [InlineKeyboardButton("👑 Admin", callback_data="menu:admin")],
        [InlineKeyboardButton("⬅️ Back to start", callback_data="menu:start")],
    ])


def back_to_help_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Back to Help", callback_data="menu:help")],
    ])


def games_keyboard():
    # Only Bet and RPS are fully wired up; rest are listed for reference/roadmap.
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎰 Bet", callback_data="game_info:bet"),
         InlineKeyboardButton("🪨📄✂️ RPS", callback_data="game_info:rps")],
        [InlineKeyboardButton("⬅️ Back to Help", callback_data="menu:help")],
    ])
