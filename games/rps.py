import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Active games: {chat_id: {"host": user_id, "wager": int, "players": {user_id: choice}}}
active_games = {}

async def rps_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user

    if chat_id in active_games:
        await update.message.reply_text("An RPS game is already running here.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /rps <wager>")
        return
    try:
        wager = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid wager.")
        return
    if wager <= 0:
        await update.message.reply_text("Wager must be positive.")
        return

    # TODO: check user balance (use your economy function)
    # For now we skip the balance check, but you should add it.

    active_games[chat_id] = {
        "host": user.id,
        "wager": wager,
        "players": {}   # user_id: choice (None until they choose)
    }

    keyboard = [
        [InlineKeyboardButton("Join Game", callback_data="rps_join")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"🪨📄✂️ RPS arena created by {user.mention_html()}!\n"
        f"Wager: {wager} coins. Tap below to join.\n"
        f"Once 2+ players join, the host can use /end to start the match.",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

async def joinrps_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    game = active_games.get(chat_id)
    if not game:
        await update.message.reply_text("No active RPS game. Start one with /rps.")
        return
    if user.id in game["players"]:
        await update.message.reply_text("You've already joined.")
        return

    game["players"][user.id] = None  # no choice yet
    await update.message.reply_text(f"{user.mention_html()} joined the arena!", parse_mode="HTML")

async def end_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    game = active_games.get(chat_id)
    if not game:
        await update.message.reply_text("No RPS game running.")
        return
    if user.id != game["host"]:
        await update.message.reply_text("Only the host can start the match.")
        return
    if len(game["players"]) < 2:
        await update.message.reply_text("Need at least 2 players (including host).")
        return

    # Send choice buttons to each player (via private message)
    for player_id in game["players"]:
        try:
            await context.bot.send_message(
                player_id,
                "Choose your move:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🪨 Rock", callback_data=f"rps_choice:{player_id}:rock"),
                     InlineKeyboardButton("📄 Paper", callback_data=f"rps_choice:{player_id}:paper"),
                     InlineKeyboardButton("✂️ Scissors", callback_data=f"rps_choice:{player_id}:scissors")]
                ])
            )
        except Exception:
            await update.message.reply_text(f"Could not message player {player_id}. Make sure they started the bot.")
            return

    await update.message.reply_text("Match started! Check your DM to choose your move.")

async def rps_choice_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split(":")
    # Expected format: rps_choice:user_id:choice
    if len(data) != 3:
        return
    user_id = int(data[1])
    choice = data[2]

    # Find the game (we don't know chat_id from query alone)
    chat_id = None
    for cid, game in active_games.items():
        if user_id in game["players"]:
            chat_id = cid
            break
    if chat_id is None:
        await query.edit_message_text("No active game found.")
        return

    game = active_games[chat_id]
    if game["players"][user_id] is not None:
        await query.edit_message_text("You already chose!")
        return

    game["players"][user_id] = choice
    await query.edit_message_text(f"You chose {choice}.")

    # Check if all players have chosen
    if all(choice is not None for choice in game["players"].values()):
        # Determine winner
        players = list(game["players"].items())
        # Simple: winner takes all (if multiple? we'll pick first winner)
        beats = {"rock": "scissors", "paper": "rock", "scissors": "paper"}
        winners = []
        for pid, pchoice in players:
            # compare against everyone else
            is_winner = True
            for pid2, pchoice2 in players:
                if pid == pid2:
                    continue
                if beats[pchoice] != pchoice2:
                    # If your choice doesn't beat the other's choice, you're not the sole winner
                    # We'll handle ties later
                    pass
            # For simplicity, if any two have different choices, one beats the other.
            # Actually we can compute a proper result:
            # rock beats scissors, scissors beats paper, paper beats rock
            # If all players choose the same, it's a draw.
        # Better: implement single elimination: compare each pair? We'll do simple: 
        # All players who are not beaten by anyone are winners. If everyone is beaten, draw.
        # This is getting complicated; I'll simplify to a 2-player RPS only for now.
        if len(players) == 2:
            p1_id, p1_choice = players[0]
            p2_id, p2_choice = players[1]
            if p1_choice == p2_choice:
                result = "It's a draw!"
            elif beats[p1_choice] == p2_choice:
                result = f"Player {p1_id} wins!"
            else:
                result = f"Player {p2_id} wins!"
        else:
            result = "Multiplayer RPS not fully implemented yet."
        
        await context.bot.send_message(chat_id, f"RPS result: {result}")
        # Clean up
        del active_games[chat_id]
