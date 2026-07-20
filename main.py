import logging

from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
)

from config import BOT_TOKEN
import database as db

from handlers import start, economy, actions, romance, admin, chat_ai
from games import bet, rps

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


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

    # Games
    app.add_handler(CommandHandler("bet", bet.bet_command))
    app.add_handler(CommandHandler("rps", rps.rps_command))
    app.add_handler(CommandHandler("joinrps", rps.joinrps_command))
    app.add_handler(CommandHandler("end", rps.end_command))
    app.add_handler(CallbackQueryHandler(rps.rps_choice_callback, pattern=r"^rps_choice:"))

    # bbet plain-text handler (must run before the generic AI chat handler)
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.Regex(r"(?i)^bbet\b"),
        bet.bbet_message_handler,
    ))

    # Catch-all AI persona chat (DMs always, groups only when mentioned/replied/random chance)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_ai.message_handler))

    return app


def main():
    app = build_app()
    logger.info("Nova is starting...")
    app.run_polling(allowed_updates=None)


if __name__ == "__main__":
    main()
