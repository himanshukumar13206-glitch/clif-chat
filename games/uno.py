import random
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackContext
import database as db

# Game state per chat: {chat_id: game_dict}
games = {}

# UNO deck
COLORS = ['r', 'g', 'b', 'y']
VALUES = ['0','1','2','3','4','5','6','7','8','9','skip','reverse','draw2']
WILD_CARDS = ['wild', 'wild4']

def build_deck():
    deck = []
    for color in COLORS:
        for value in VALUES:
            deck.append(f"{color}_{value}")
            if value != '0':   # one 0 per color, two of others
                deck.append(f"{color}_{value}")
    for _ in range(4):
        deck.append('wild')
        deck.append('wild4')
    random.shuffle(deck)
    return deck

def card_display(card: str):
    """Human readable representation."""
    if card in ('wild', 'wild4'):
        return '🃏 Wild' if card=='wild' else '+4'
    color, value = card.split('_')
    color_emoji = {'r':'🔴','g':'🟢','b':'🔵','y':'🟡'}.get(color, '')
    return f"{color_emoji} {value}"

def card_to_sticker(card: str) -> str | None:
    """Return sticker file_id if saved, else None."""
    return db.get_uno_sticker(card)

async def uno_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    if chat_id in games:
        await update.message.reply_text("A game is already running in this chat.")
        return
    games[chat_id] = {
        'creator': user.id,
        'players': {},        # user_id: {'hand': list, 'called_uno': False}
        'deck': [],
        'discard': [],
        'current_player': None,
        'direction': 1,
        'turn_timeout': 90,
        'started': False,
        'turn_task': None
    }
    await update.message.reply_text(
        f"🃏 UNO created by {user.mention_html()}!\n"
        "Others: /unojoin to join.\n"
        "When ready, the creator can /unostartgame to begin.",
        parse_mode='HTML'
    )

async def uno_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    game = games.get(chat_id)
    if not game:
        await update.message.reply_text("No game running. Start with /unostart.")
        return
    if game['started']:
        await update.message.reply_text("Game already in progress. Wait for next round.")
        return
    if user.id in game['players']:
        await update.message.reply_text("You're already in.")
        return
    game['players'][user.id] = {'hand': [], 'called_uno': False}
    await update.message.reply_text(f"{user.mention_html()} joined! Players: {len(game['players'])}", parse_mode='HTML')

async def uno_start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    game = games.get(chat_id)
    if not game:
        await update.message.reply_text("No game. Create one with /unostart.")
        return
    if user.id != game['creator']:
        await update.message.reply_text("Only the game creator can start the game.")
        return
    if len(game['players']) < 2:
        await update.message.reply_text("Need at least 2 players.")
        return

    # Initialize deck and hands
    game['deck'] = build_deck()
    # Deal 7 cards to each player
    for uid in game['players']:
        game['players'][uid]['hand'] = [game['deck'].pop() for _ in range(7)]
    # Start discard pile
    game['discard'] = [game['deck'].pop()]
    # Set first player (creator)
    game['current_player'] = game['creator']
    game['direction'] = 1
    game['started'] = True

    # Notify each player privately with their hand
    for uid, pdata in game['players'].items():
        try:
            await context.bot.send_message(uid, "Your UNO hand:", reply_markup=await hand_keyboard(uid, game))
        except Exception:
            pass
    await update.message.reply_text("Game started! Check your private messages to play.")

    # Start turn timer
    game['turn_task'] = asyncio.create_task(turn_timer(chat_id, context))

async def hand_keyboard(user_id: int, game: dict):
    """Build inline keyboard for the player's hand."""
    hand = game['players'][user_id]['hand']
    buttons = []
    for idx, card in enumerate(hand):
        display = card_display(card)
        sticker_id = card_to_sticker(card)
        if sticker_id:
            # We can't send sticker directly in callback button; use text fallback.
            # However, we could send a separate sticker message. For now, text.
            pass
        buttons.append([InlineKeyboardButton(f"{display}", callback_data=f"uno_play:{idx}")])
    # Extra options
    buttons.append([InlineKeyboardButton("🃏 Draw card", callback_data="uno_draw"),
                    InlineKeyboardButton("❓ State", callback_data="uno_state")])
    return InlineKeyboardMarkup(buttons)

async def uno_play_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = query.from_user
    chat_id = None
    # Find chat_id for this user
    for cid, game in games.items():
        if user.id in game['players']:
            chat_id = cid
            break
    if not chat_id:
        await query.edit_message_text("You're not in a game.")
        return
    game = games[chat_id]

    # Check if it's this player's turn
    if game['current_player'] != user.id:
        await query.edit_message_text("It's not your turn.")
        return

    if data.startswith("uno_play:"):
        idx = int(data.split(":")[1])
        hand = game['players'][user.id]['hand']
        if idx >= len(hand):
            await query.edit_message_text("Invalid card.")
            return
        card = hand[idx]
        if not can_play(card, game):
            await query.edit_message_text("You can't play that card right now.")
            return
        # Play card
        play_card(card, user.id, game, chat_id, context)
        hand.pop(idx)
        await query.edit_message_text(f"You played {card_display(card)}.")
        await next_turn(chat_id, context)
    elif data == "uno_draw":
        if not game['deck']:
            reshuffle_discard(game)
        drawn = game['deck'].pop()
        game['players'][user.id]['hand'].append(drawn)
        await query.edit_message_text(f"You drew a card. Your hand:", reply_markup=await hand_keyboard(user.id, game))
    elif data == "uno_state":
        # Show current game state
        state = f"Current card: {card_display(game['discard'][-1])}\n"
        state += f"Player turn: {game['current_player']}\n"
        await query.edit_message_text(state, reply_markup=await hand_keyboard(user.id, game))

def can_play(card: str, game: dict) -> bool:
    """Check if card can be played on current discard."""
    top = game['discard'][-1]
    if card in ('wild', 'wild4'):
        return True
    card_color, card_val = card.split('_')
    if top in ('wild', 'wild4'):
        # Wild played, color chosen is stored elsewhere? We'll store chosen_color in game
        return card_color == game.get('chosen_color', '')
    top_color, top_val = top.split('_')
    return card_color == top_color or card_val == top_val

def play_card(card: str, user_id: int, game: dict, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Add card to discard and handle special cards."""
    game['discard'].append(card)
    # Handle special cards
    if 'draw2' in card:
        next_player = get_next_player(game)
        draw_cards(game, next_player, 2)
    elif 'wild4' in card:
        # Let player choose color via another callback, temporarily skip
        pass
    # check win
    if len(game['players'][user_id]['hand']) == 0:
        # winner!
        asyncio.create_task(declare_winner(chat_id, user_id, context))
        return

async def declare_winner(chat_id, winner_id, context):
    game = games.pop(chat_id, None)
    if game and game['turn_task']:
        game['turn_task'].cancel()
    winner = await context.bot.get_chat(winner_id)
    await context.bot.send_message(chat_id, f"{winner.mention_html()} wins the game! 🎉", parse_mode='HTML')

def get_next_player(game: dict) -> int:
    players = list(game['players'].keys())
    idx = players.index(game['current_player'])
    direction = game['direction']
    next_idx = (idx + direction) % len(players)
    return players[next_idx]

def draw_cards(game: dict, player_id: int, count: int):
    for _ in range(count):
        if not game['deck']:
            reshuffle_discard(game)
        game['players'][player_id]['hand'].append(game['deck'].pop())

def reshuffle_discard(game: dict):
    top = game['discard'].pop()
    game['deck'].extend(game['discard'])
    random.shuffle(game['deck'])
    game['discard'] = [top]

async def next_turn(chat_id, context):
    game = games.get(chat_id)
    if not game or not game['started']:
        return
    # Determine next player
    game['current_player'] = get_next_player(game)
    # Cancel old timer
    if game['turn_task']:
        game['turn_task'].cancel()
    game['turn_task'] = asyncio.create_task(turn_timer(chat_id, context))
    # Notify next player
    next_uid = game['current_player']
    try:
        await context.bot.send_message(next_uid, "It's your turn!", reply_markup=await hand_keyboard(next_uid, game))
    except Exception:
        pass

async def turn_timer(chat_id, context):
    await asyncio.sleep(90)
    game = games.get(chat_id)
    if game and game['started']:
        # Skip current player
        skipped = game['current_player']
        await context.bot.send_message(chat_id, f"Player {skipped} took too long, skipping...")
        await next_turn(chat_id, context)

# Admin commands
async def uno_skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    game = games.get(chat_id)
    if not game or not game['started']:
        await update.message.reply_text("No active game.")
        return
    game['turn_task'].cancel()
    await update.message.reply_text("Turn skipped.")
    await next_turn(chat_id, context)

async def uno_leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # remove player, if game empty, kill
    pass

async def uno_kill(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    game = games.get(chat_id)
    if not game or user.id != game['creator']:
        await update.message.reply_text("Only the game creator can kill the game.")
        return
    if game['turn_task']:
        game['turn_task'].cancel()
    del games[chat_id]
    await update.message.reply_text("Game terminated.")

# Sticker setup (sudo only)
async def set_uno_stickers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not db.is_sudo(user.id):
        await update.message.reply_text("Only bot admins can set stickers.")
        return
    await update.message.reply_text(
        "Send me the sticker for each UNO card. Reply to this message with the sticker, "
        "and use the caption to write the card name (e.g., r_0, g_skip, wild4).\n"
        "You can do one at a time. When done, send /done_stickers."
    )
    context.user_data['awaiting_sticker'] = True

async def handle_sticker_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('awaiting_sticker'):
        return
    msg = update.message
    if not msg.sticker:
        await msg.reply_text("Please send a sticker.")
        return
    card_name = msg.caption or ""
    if not card_name:
        await msg.reply_text("The sticker caption must be the card name (e.g., r_0).")
        return
    db.save_uno_sticker(card_name.strip(), msg.sticker.file_id)
    await msg.reply_text(f"Sticker for {card_name} saved!")

async def done_stickers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['awaiting_sticker'] = False
    await update.message.reply_text("Sticker setup complete.")
