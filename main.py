import logging
import asyncio
import signal
import os
from asyncio import start_server

from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
)

from config import BOT_TOKEN
import database as db

from handlers import start, economy, actions, romance, admin, chat_ai
from games import bet, rps, mines, wordchain, uno

# ========== Tagall & Festival imports ==========
from handlers.tagall import (
    tag_all, tag_one_by_one, tag_all_in_one,
    good_morning, good_night, festivals_menu,
    today_festival, all_festivals, tagall_back,
    new_member, left_member
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# --- Health check for Render ---
async def health_check_handler(reader, writer):
    response = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Length: 2\r\n"
        "Content-Type: text/plain\r\n"
        "Connection: close\r\n"
        "\r\n"
        "OK"
    )
    writer.write(response.encode())
    await writer.drain()
    writer.close()
    await writer.wait_closed()


# ========== /start : Photo + Original Nova welcome ==========
async def start_with_photo(update, context):
    # 1. Send the welcome photo (replace placeholder with your real file_id later)
    await update.message.reply_photo(
        photo="PASTE_YOUR_FILE_ID_HERE",   # <-- change this after you get the correct ID
        caption=""
    )
    # 2. Then send the original rich welcome message + keyboard
    await start.start_command(update, context)


# ========== /getid – get your bot's own photo file_id ==========
async def get_photo_id(update, context):
    """Extract file_id from the photo this command is replying to."""
    # Check if the command is a reply to a photo
    if update.message.reply_to_message and update.message.reply_to_message.photo:
        file_id = update.message.reply_to_message.photo[-1].file_id
        await update.message.reply_text(
            f"✅ Your file_id:\n`{file_id}`",
            parse_mode='Markdown'
        )
        return
    # Fallback: if the command message itself contains a photo (unlikely)
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        await update.message.reply_text(
            f"✅ Your file_id:\n`{file_id}`",
            parse_mode='Markdown'
        )
        return
    await update.message.reply_text("Reply to a photo with /getid to get its file_id.")


# --- /rules (unchanged) ---
async def rules_command(update, context):
    rules_text = (
        "🎮 <b>Game Rules</b>\n\n"
        "🎰 <b>/bet &lt;amount&gt;</b> – Solo gambling. 50% chance to double your money.\n"
        "   or use: <code>bbet 100</code> in any chat.\n\n"
        "🪨📄✂️ <b>/rps &lt;wager&gt;</b> – Multiplayer rock‑paper‑scissors.\n"
        "   • <b>/joinrps</b> to join\n"
        "   • Host can type <b>/end</b> to start the match\n"
        "   • Each player chooses via private message buttons.\n\n"
        "💣 <b>/mines</b> – Reveal safe tiles (numbers 1‑25), avoid 3 hidden bombs.\n"
        "   • Each safe tile gives +10 points.\n"
        "   • <b>/stopmines</b> to quit.\n\n"
        "🔗 <b>/wordchain</b> – Start a word chain in the group.\n"
        "   • The next word must begin with the last letter of the previous.\n"
        "   • No repeats allowed!\n"
        "   • <b>/stopchain</b> to end.\n\n"
        "🃏 <b>UNO</b> (full game)\n"
        "   • <b>/unostart</b> – Create a game lobby.\n"
        "   • <b>/unojoin</b> – Join the lobby.\n"
        "   • <b>/unostartgame</b> – (creator only) Start the game.\n"
        "   • Play cards in your private chat – inline buttons appear.\n"
        "   • <b>/unoleave</b> – Leave the game.\n"
        "   • <b>/unoskip</b> – Skip the current player (after 90s).\n"
        "   • <b>/unokill</b> – (creator only) Terminate the game.\n"
        "   • <b>/setunostickers</b> – (sudo only) Upload sticker pack for cards.\n"
    )
    await update.message.reply_html(rules_text)


def build_app():
    db.init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    # /start (photo + original welcome)
    app.add_handler(CommandHandler("start", start_with_photo))

    app.add_handler(CallbackQueryHandler(start.menu_callback, pattern=r"^menu:"))
    app.add_handler(CallbackQueryHandler(start.game_info_callback, pattern=r"^game_info:"))

    # Chat prefs
    app.add_handler(CommandHandler("checkins", chat_ai.checkins_command))
    app.add_handler(CommandHandler("reactions", chat_ai.reactions_command))
    app.add_handler(CommandHandler("quiet", chat_ai.quiet_command))
    app.add_handler(CommandHandler("chatty", chat_ai.chatty_command))

    # Economy
    app.add_handler(CommandHandler(["balance", "bal"], economy.balance_command))
    app.add_handler(CommandHandler("daily", economy.daily_command))
    app.add_handler(CommandHandler("give", economy.give_command))
    app.add_handler(CommandHandler(["toprich", "leaderboard"], economy.toprich_command))
    app.add_handler(CommandHandler("rank", economy.rank_command))

    # Actions
    app.add_handler(CommandHandler("rob", actions.rob_command))
    app.add_handler(CommandHandler("kill", actions.kill_command))
    app.add_handler(CommandHandler("protect", actions.protect_command))
    app.add_handler(CommandHandler(["shield", "protection"], actions.shield_command))
    app.add_handler(CommandHandler("revive", actions.revive_command))
    app.add_handler(CommandHandler("topkill", actions.topkill_command))

    # Romance
    app.add_handler(CommandHandler("propose", romance.propose_command))
    app.add_handler(CommandHandler("divorce", romance.divorce_command))
    app.add_handler(CommandHandler(["marriage", "married"], romance.marriage_command))
    app.add_handler(CommandHandler(["couple", "shippering"], romance.couple_command))

    # Admin / sudo / auth
    app.add_handler(CommandHandler("addsudo", admin.addsudo_command))
    app.add_handler(CommandHandler("delsudo", admin.delsudo_command))
    app.add_handler(CommandHandler("sudolist", admin.sudolist_command))
    app.add_handler(CommandHandler("auth", admin.auth_command))
    app.add_handler(CommandHandler("unauth", admin.unauth_command))
    app.add_handler(CommandHandler("authlist", admin.authlist_command))
    app.add_handler(CommandHandler("groupbot", admin.groupbot_command))
    app.add_handler(CommandHandler("groupmode", admin.groupmode_command))

    # ===== Existing Games =====
    app.add_handler(CommandHandler("bet", bet.bet_command))
    app.add_handler(CommandHandler("rps", rps.rps_command))
    app.add_handler(CommandHandler("joinrps", rps.joinrps_command))
    app.add_handler(CommandHandler("end", rps.end_command))
    app.add_handler(CallbackQueryHandler(rps.rps_choice_callback, pattern=r"^rps_choice:"))

    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.Regex(r"(?i)^bbet\b"),
        bet.bbet_message_handler,
    ))

    # Mines & Wordchain
    app.add_handler(CommandHandler("mines", mines.mines_command))
    app.add_handler(CommandHandler("stopmines", mines.stop_mines))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.Regex(r"^\d+$") & filters.ChatType.GROUPS,
        mines.mines_tile_handler,
    ))

    app.add_handler(CommandHandler("wordchain", wordchain.wordchain_start))
    app.add_handler(CommandHandler("stopchain", wordchain.stop_chain))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
        wordchain.wordchain_handler,
    ))

    # UNO Game
    app.add_handler(CommandHandler("unostart", uno.uno_start))
    app.add_handler(CommandHandler("unojoin", uno.uno_join))
    app.add_handler(CommandHandler("unostartgame", uno.uno_start_game))
    app.add_handler(CommandHandler("unoleave", uno.uno_leave))
    app.add_handler(CommandHandler("unoskip", uno.uno_skip))
    app.add_handler(CommandHandler("unokill", uno.uno_kill))
    app.add_handler(CommandHandler("setunostickers", uno.set_uno_stickers))
    app.add_handler(CommandHandler("done_stickers", uno.done_stickers))
    app.add_handler(CallbackQueryHandler(uno.uno_play_callback, pattern=r"^uno_play:"))
    app.add_handler(CallbackQueryHandler(uno.uno_play_callback, pattern=r"^uno_draw$"))
    app.add_handler(CallbackQueryHandler(uno.uno_play_callback, pattern=r"^uno_state$"))
    app.add_handler(MessageHandler(
        filters.Sticker.ALL & ~filters.COMMAND,
        uno.handle_sticker_message
    ), group=1)

    # ===== Tagall & Festival handlers =====
    app.add_handler(CommandHandler("tagall", tag_all))
    app.add_handler(CallbackQueryHandler(tag_one_by_one, pattern="^tag_one$"))
    app.add_handler(CallbackQueryHandler(tag_all_in_one, pattern="^tag_all_in_one$"))
    app.add_handler(CallbackQueryHandler(good_morning, pattern="^good_morning$"))
    app.add_handler(CallbackQueryHandler(good_night, pattern="^good_night$"))
    app.add_handler(CallbackQueryHandler(festivals_menu, pattern="^festivals_menu$"))
    app.add_handler(CallbackQueryHandler(today_festival, pattern="^today_festival$"))
    app.add_handler(CallbackQueryHandler(all_festivals, pattern="^all_festivals$"))
    app.add_handler(CallbackQueryHandler(tagall_back, pattern="^tagall_back$"))

    # Group member tracking
    app.add_handler(MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member
    ))
    app.add_handler(MessageHandler(
        filters.StatusUpdate.LEFT_CHAT_MEMBER, left_member
    ))

    # Temporary /getid (remove after you get the correct file_id)
    app.add_handler(CommandHandler("getid", get_photo_id))

    # Rules command
    app.add_handler(CommandHandler("rules", rules_command))

    # Catch-all AI chat (MUST BE LAST)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_ai.message_handler))

    return app


async def main():
    app = build_app()
    logger.info("Nova is starting...")

    await app.initialize()
    await app.updater.start_polling()
    await app.start()
    logger.info("Nova is running.")

    port = int(os.environ.get("PORT", 10000))
    server = await start_server(health_check_handler, host="0.0.0.0", port=port)
    logger.info(f"Health check server listening on port {port}")

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    def stop():
        logger.info("Shutting down...")
        stop_event.set()

    loop.add_signal_handler(signal.SIGTERM, stop)
    loop.add_signal_handler(signal.SIGINT, stop)

    await stop_event.wait()

    server.close()
    await server.wait_closed()
    await app.stop()
    await app.updater.stop()
    await app.shutdown()
    logger.info("Nova has stopped.")


if __name__ == "__main__":
    asyncio.run(main())
