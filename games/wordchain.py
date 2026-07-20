from telegram import Update
from telegram.ext import ContextTypes

chains = {}

async def wordchain_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in chains:
        await update.message.reply_text("A word chain is already active.")
        return
    chains[chat_id] = {"last": None, "used": set()}
    await update.message.reply_text(
        "🔗 Wordchain started! Send a word.\n"
        "Next word must start with the last letter of the previous word.\n"
        "No repeats! Type /stopchain to end."
    )

async def wordchain_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chain = chains.get(chat_id)
    if not chain:
        return
    word = update.message.text.strip().lower()
    if not word.isalpha():
        return
    if chain["last"] and word[0] != chain["last"][-1]:
        await update.message.reply_text(f"❌ Must start with '{chain['last'][-1]}'.")
        return
    if word in chain["used"]:
        await update.message.reply_text("❌ Word already used.")
        return
    chain["last"] = word
    chain["used"].add(word)
    await update.message.reply_text(f"✅ {word} accepted!")

async def stop_chain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in chains:
        del chains[chat_id]
        await update.message.reply_text("Wordchain stopped.")
    else:
        await update.message.reply_text("No active wordchain.")
