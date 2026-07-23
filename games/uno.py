# games/uno.py
import logging
from uuid import uuid4
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

# Import the actual game engine from the submodule
from games.uno.game import MauMau
from games.uno.player import Player
from games.uno.database import GameDatabase
from games.uno import config   # if needed for constants

logger = logging.getLogger(__name__)

# Simple in‑memory store for active games (game_id -> MauMau instance)
games = {}

# ----------------------------------------------------------------------
# Command handlers
# ----------------------------------------------------------------------

async def uno_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create a new UNO lobby (/unostart)"""
    chat_id = update.effective_chat.id
    if any(g for g in games.values() if g.chat.id == chat_id and not g.started):
        await update.message.reply_text("A game is already waiting in this chat!")
        return

    # Create a new game using the MauMau class from the submodule
    game = MauMau()  # we'll need to set chat, etc. See below
    game.chat = update.effective_chat    # store the chat object (needed later)
    game.starter = update.effective_user
    game.owner.append(update.effective_user.id)
    game.mode = "classic"   # default mode

    game_id = str(uuid4())[:8]
    games[game_id] = game

    await update.message.reply_text(
        f"🃏 UNO lobby created!\n"
        f"Game ID: `{game_id}`\n"
        f"Creator: {update.effective_user.mention_html()}\n\n"
        f"Join with /unojoin {game_id}",
        parse_mode="HTML"
    )

async def uno_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Join an existing lobby (/unojoin <game_id>)"""
    if not context.args:
        await update.message.reply_text("Usage: /unojoin <game_id>")
        return

    game_id = context.args[0]
    game = games.get(game_id)
    if not game:
        await update.message.reply_text("Game not found.")
        return

    user = update.effective_user
    # Check if already joined
    if any(p.user.id == user.id for p in game.players):
        await update.message.reply_text("You already joined this game.")
        return

    player = Player(user.id, user.first_name)
    game.add_player(player)

    players_list = ", ".join(p.name for p in game.players)
    await update.message.reply_text(
        f"✅ {user.mention_html()} joined!\n"
        f"Players ({len(game.players)}): {players_list}",
        parse_mode="HTML"
    )

async def uno_start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the game (creator only)"""
    # We need to find the game where user is creator and not started
    user = update.effective_user
    for game in games.values():
        if game.starter.id == user.id and not game.started:
            if len(game.players) < 2:
                await update.message.reply_text("Need at least 2 players to start.")
                return
            game.start()
            # Deal cards (the game engine does that)
            for player in game.players:
                player.draw_first_hand()

            # Send the first card and a "Make your choice" button
            first_card = game.last_card
            await context.bot.send_sticker(
                chat_id=game.chat.id,
                sticker=game.stickers.get(str(first_card), "CAACAgIAAxkBAA...")  # need a default sticker
            )
            # Build inline keyboard for the current player
            kb = build_play_keyboard(game.current_player)
            await context.bot.send_message(
                chat_id=game.chat.id,
                text=f"First player: {game.current_player.name}\n"
                     f"Current card: {first_card}",
                reply_markup=kb
            )
            return
    await update.message.reply_text("You don't have a waiting lobby to start.")

async def uno_leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Leave a game"""
    # Find the player's game
    user = update.effective_user
    for game in games.values():
        player = next((p for p in game.players if p.user.id == user.id), None)
        if player:
            game.remove_player(player)
            await update.message.reply_text("You left the game.")
            if not game.players:
                # remove game if empty
                for gid, g in list(games.items()):
                    if g == game:
                        del games[gid]
            return
    await update.message.reply_text("You are not in any game.")

async def uno_skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Skip the current player (admin/creator only)"""
    # Simplified: find the game where the user is creator/admin and force skip
    user = update.effective_user
    for game in games.values():
        if game.started and user.id in game.owner:
            # use the game's turn logic
            game.turn()
            await update.message.reply_text("Turn skipped.")
            # update display
            await update_game_display(context.bot, game)
            return
    await update.message.reply_text("You can't skip right now.")

async def uno_kill(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kill a game (creator only)"""
    user = update.effective_user
    for gid, game in list(games.items()):
        if user.id in game.owner:
            del games[gid]
            await update.message.reply_text("Game terminated.")
            return
    await update.message.reply_text("No game to kill or you're not the owner.")

# ----------------------------------------------------------------------
# Callback query handler (inline buttons for playing)
# ----------------------------------------------------------------------

async def uno_play_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all UNO inline button presses."""
    query = update.callback_query
    await query.answer()
    data = query.data
    user = query.from_user

    # Identify the game and player
    game = None
    player = None
    for g in games.values():
        for p in g.players:
            if p.user.id == user.id:
                game = g
                player = p
                break
        if game:
            break

    if not game or not player:
        await query.edit_message_text("You are not in an active game.")
        return

    if data == "uno_draw":
        if not player.drew:
            player.draw()
            await query.edit_message_text("You drew a card. Now play or pass.")
            # update keyboard to show pass
            kb = build_play_keyboard(player, can_pass=True)
            await query.edit_message_reply_markup(reply_markup=kb)
            return
        else:
            # already drew, pass
            game.turn()
            await update_game_display(context.bot, game)
            return
    elif data == "uno_pass":
        game.turn()
        await update_game_display(context.bot, game)
        return
    elif data.startswith("uno_play:"):
        card_str = data.split(":", 1)[1]
        # try to play that card
        try:
            game.play_card(player, card_str)
        except Exception as e:
            await query.answer(f"Can't play that card: {e}", show_alert=True)
            return
        # Send updated game state
        await update_game_display(context.bot, game)
    elif data == "uno_state":
        # just refresh the keyboard (maybe)
        kb = build_play_keyboard(player)
        await query.edit_message_reply_markup(reply_markup=kb)
        return

# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def build_play_keyboard(player, can_pass=False):
    """Build an inline keyboard for the player's hand."""
    buttons = []
    # Group cards by color (simplified)
    for card in player.cards:
        cb = f"uno_play:{str(card)}"
        if card in player.playable_cards():
            buttons.append(InlineKeyboardButton(str(card), callback_data=cb))
        else:
            buttons.append(InlineKeyboardButton(f"❌{str(card)}", callback_data="none"))
    # Add draw / pass / state
    extra = []
    if not player.drew:
        extra.append(InlineKeyboardButton("🃏 Draw", callback_data="uno_draw"))
    if can_pass:
        extra.append(InlineKeyboardButton("⏭ Pass", callback_data="uno_pass"))
    extra.append(InlineKeyboardButton("🔄 Refresh", callback_data="uno_state"))
    layout = [buttons[i:i+3] for i in range(0, len(buttons), 3)]  # 3 per row
    layout.append(extra)
    return InlineKeyboardMarkup(layout)

async def update_game_display(bot, game):
    """Send a message with current top card and next player's hand."""
    # Send sticker for current top card
    await bot.send_sticker(
        chat_id=game.chat.id,
        sticker=game.stickers.get(str(game.last_card), "default_sticker_file_id")
    )
    kb = build_play_keyboard(game.current_player)
    await bot.send_message(
        chat_id=game.chat.id,
        text=f"Current: {game.last_card}\n"
             f"It's {game.current_player.name}'s turn.",
        reply_markup=kb
    )

# ----------------------------------------------------------------------
# Sticker setup (simple placeholder)
# ----------------------------------------------------------------------

async def set_uno_stickers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Sticker setup not yet implemented.")

async def done_stickers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Sticker setup finished (dummy).")

async def handle_sticker_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass  # not used now