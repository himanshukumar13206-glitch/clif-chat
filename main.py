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
from games import bet, rps, mines, wordchain, uno   # <-- new games imported

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# --- Minimal HTTP handler for Render health check ---
async def health_check_handler(reader, writer):
    """Respond with a simple 200 OK."""
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


# --- Simple /rules command (add this function) ---
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
        "🃏 <b>/unostart</b> – Create an UNO lobby (basic version).\n"
        "   • <b>/unojoin</b> to join.\n"
        "   • Owner can set sticker packs with <b>/unostickers</b> (coming soon).\n"
    )
    await update.message.reply_html(rules_text)


def build_app():
    db.init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    # Start / help menus
    app.add_handler(CommandHandler("start", start.start_command))
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

    # ===== EXISTING GAMES (bet, rps) =====
    app.add_handler(CommandHandler("bet", bet.bet_command))
    app.add_handler(CommandHandler("rps", rps.rps_command))
    app.add_handler(CommandHandler("joinrps", rps.joinrps_command))
    app.add_handler(CommandHandler("end", rps.end_command))
    app.add_handler(CallbackQueryHandler(rps.rps_choice_callback, pattern=r"^rps_choice:"))

    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.Regex(r"(?i)^bbet\b"),
        bet.bbet_message_handler,
    ))

    # ===== NEW GAMES =====
    # Mines
    app.add_handler(CommandHandler("mines", mines.mines_command))
    app.add_handler(CommandHandler("stopmines", mines.stop_mines))
    # Number inputs for mines (only in groups to avoid clashes with private chats)
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.Regex(r"^\d+$") & filters.ChatType.GROUPS,
        mines.mines_tile_handler,
    ))

    # Wordchain
    app.add_handler(CommandHandler("wordchain", wordchain.wordchain_start))
    app.add_handler(CommandHandler("stopchain", wordchain.stop_chain))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
        wordchain.wordchain_handler,
    ))

    # UNO (lobby)
    app.add_handler(CommandHandler("unostart", uno.uno_start))
    app.add_handler(CommandHandler("unojoin", uno.uno_join))
    app.add_handler(CommandHandler("unostickers", uno.uno_set_stickers))

    # Rules command
    app.add_handler(CommandHandler("rules", rules_command))

    # Catch-all AI persona chat (ALWAYS LAST)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_ai.message_handler))

    return app


async def main():
    app = build_app()
    logger.info("Nova is starting...")

    # Start the bot
    await app.initialize()
    await app.updater.start_polling()
    await app.start()
    logger.info("Nova is running.")

    # Start the tiny HTTP server for Render's health check
    port = int(os.environ.get("PORT", 10000))
    server = await start_server(health_check_handler, host="0.0.0.0", port=port)
    logger.info(f"Health check server listening on port {port}")

    # Wait until a stop signal
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    def stop():
        logger.info("Shutting down...")
        stop_event.set()

    loop.add_signal_handler(signal.SIGTERM, stop)
    loop.add_signal_handler(signal.SIGINT, stop)

    await stop_event.wait()

    # Graceful shutdown
    server.close()
    await server.wait_closed()
    await app.stop()
    await app.updater.stop()
    await app.shutdown()
    logger.info("Nova has stopped.")


if __name__ == "__main__":
    asyncio.run(main())
