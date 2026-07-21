from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def start_keyboard(bot_username: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Chat with me", callback_data="menu:chat")],
        [InlineKeyboardButton("📖 Help & Commands", callback_data="menu:help"),
         InlineKeyboardButton("🎮 Games", callback_data="menu:games")],   # <-- NEW direct Games button
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
    # 40+ game buttons – currently playable ones are mixed with roadmap placeholders
    return InlineKeyboardMarkup([
        # First row: games that are already fully playable
        [InlineKeyboardButton("🎰 Bet", callback_data="game_info:bet"),
         InlineKeyboardButton("🪨📄✂️ RPS", callback_data="game_info:rps")],
        [InlineKeyboardButton("💣 Mines", callback_data="game_info:mines"),
         InlineKeyboardButton("🔗 Wordchain", callback_data="game_info:wordchain")],
        [InlineKeyboardButton("🃏 UNO", callback_data="game_info:uno")],

        # Roadmap games (coming soon)
        [InlineKeyboardButton("♟️ Chess", callback_data="game_info:chess"),
         InlineKeyboardButton("🎯 Darts", callback_data="game_info:darts")],
        [InlineKeyboardButton("🎲 Dice", callback_data="game_info:dice"),
         InlineKeyboardButton("🃏 Blackjack", callback_data="game_info:blackjack")],
        [InlineKeyboardButton("🎰 Slots", callback_data="game_info:slots"),
         InlineKeyboardButton("🧩 Wordgrid", callback_data="game_info:wordgrid")],
        [InlineKeyboardButton("🕵️ Hack", callback_data="game_info:hack"),
         InlineKeyboardButton("🃏 Cards", callback_data="game_info:cards")],
        [InlineKeyboardButton("🏓 Ping Pong", callback_data="game_info:pingpong"),
         InlineKeyboardButton("🎳 Bowling", callback_data="game_info:bowling")],
        [InlineKeyboardButton("🏀 Basketball", callback_data="game_info:basketball"),
         InlineKeyboardButton("⚽ Football", callback_data="game_info:football")],
        [InlineKeyboardButton("🎱 Pool", callback_data="game_info:pool"),
         InlineKeyboardButton("🎯 Archery", callback_data="game_info:archery")],
        [InlineKeyboardButton("🏹 Duel", callback_data="game_info:duel"),
         InlineKeyboardButton("🧠 Quiz", callback_data="game_info:quiz")],
        [InlineKeyboardButton("📝 Hangman", callback_data="game_info:hangman"),
         InlineKeyboardButton("🔢 2048", callback_data="game_info:2048")],
        [InlineKeyboardButton("🕹️ TicTacToe", callback_data="game_info:tictactoe"),
         InlineKeyboardButton("🎮 Snake", callback_data="game_info:snake")],
        [InlineKeyboardButton("🧊 Tetris", callback_data="game_info:tetris"),
         InlineKeyboardButton("🚀 Space", callback_data="game_info:space")],
        [InlineKeyboardButton("🔫 Shooter", callback_data="game_info:shooter"),
         InlineKeyboardButton("🏆 Racing", callback_data="game_info:racing")],
        [InlineKeyboardButton("🎣 Fishing", callback_data="game_info:fishing"),
         InlineKeyboardButton("🏡 Farm", callback_data="game_info:farm")],
        [InlineKeyboardButton("🛒 Shop", callback_data="game_info:shop"),
         InlineKeyboardButton("💎 Miner", callback_data="game_info:miner")],
        [InlineKeyboardButton("🧪 Craft", callback_data="game_info:craft"),
         InlineKeyboardButton("🗺️ Explore", callback_data="game_info:explore")],
        [InlineKeyboardButton("🔍 Detective", callback_data="game_info:detective"),
         InlineKeyboardButton("🎭 Roleplay", callback_data="game_info:roleplay")],
        [InlineKeyboardButton("🎤 Karaoke", callback_data="game_info:karaoke"),
         InlineKeyboardButton("🎬 Movie", callback_data="game_info:movie")],
        [InlineKeyboardButton("📺 Series", callback_data="game_info:series")],

        # Back button at the end
        [InlineKeyboardButton("⬅️ Back to Help", callback_data="menu:help")],
    ])
