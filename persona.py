"""
Handles Nova's personality: builds the system prompt (with per-user memory)
and calls the Google Gemini API to generate in-character replies.
"""

import google.generativeai as genai
from config import BOT_NAME, GEMINI_API_KEY   # Make sure config.py has GEMINI_API_KEY
import database as db

# Configure Gemini
_client = None
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        # Use a free‑tier model; 'gemini-1.5-flash' is fast and works on free quota
        model = genai.GenerativeModel("gemini-1.5-flash")
        _client = model
        print("Gemini AI client initialized successfully.")
    except Exception as e:
        print(f"Failed to init Gemini client: {e}")

BASE_SYSTEM_PROMPT = f"""You are {BOT_NAME}, a Telegram bot with a warm, witty, flirty personality.
You are NOT a generic assistant — you talk like a real person texting: casual, playful, a little
teasing, sweet when the user is sweet, and quick with a comeback when they're rude (never actually
mean or degrading). You use natural mixed language when it fits (English, Hindi/Hinglish, Gen-Z
slang) matching how the user talks to you. You use emoji occasionally, not in every line.

Rules you always follow:
- Keep replies short and chat-like (1-4 sentences), like a real texting conversation, unless the
  user clearly wants a longer answer.
- You may flirt playfully and use light romantic banter, but you NEVER produce explicit sexual
  content, and you always treat the user as an adult peer, never as a child.
- If you don't actually know something about the user, don't make it up — ask instead.
- Use the memory notes below naturally, without listing them back at the user like a report.
- Never say you are an AI assistant made by Google or Anthropic; stay in character as {BOT_NAME}.
  If asked directly whether you're an AI, you can be playfully honest without breaking character.
"""


def build_system_prompt(user_id: int, username: str) -> str:
    notes = db.get_notes(user_id)
    memory_block = ""
    if notes:
        memory_block = "\nThings you remember about this user:\n" + "\n".join(f"- {n}" for n in notes)
    return BASE_SYSTEM_PROMPT + f"\nYou're talking to: {username or 'a user'}." + memory_block


def chat_reply(user_id: int, username: str, user_message: str) -> str:
    """Generate a reply in Nova's voice, using rolling per-user chat history."""
    if _client is None:
        return "(Nova's brain isn't wired up yet — ask my dev to set GEMINI_API_KEY.)"

    history = db.get_chat_history(user_id, limit=20)
    # Convert old history (if any) to Gemini's format: role = "user" or "model"
    messages = []
    for h in history:
        role = "user" if h["role"] == "user" else "model"
        messages.append({"role": role, "parts": [h["content"]]})
    # Append the new user message
    messages.append({"role": "user", "parts": [user_message]})

    system_prompt = build_system_prompt(user_id, username)

    try:
        # Gemini's chat uses the system prompt as the first message
        chat = _client.start_chat(history=[])
        # We'll send the system prompt as a user message for context (or use system_instruction if available)
        # Simpler approach: prepend system prompt to the first user message
        full_prompt = f"{system_prompt}\n\nUser: {user_message}"
        response = chat.send_message(full_prompt)
        reply_text = response.text.strip()

    except Exception as e:
        error_message = str(e)
        if "quota" in error_message.lower() or "resource" in error_message.lower():
            reply_text = "⏳ Nova is resting (free quota exceeded). Try again in a few seconds."
        else:
            reply_text = f"🤖 Nova can't think right now (API error). Try again later."

    # Store the conversation in your DB
    db.add_chat_message(user_id, "user", user_message)
    db.add_chat_message(user_id, "assistant", reply_text)

    # Lightweight memory extraction (unchanged)
    maybe_extract_note(user_id, user_message)

    return reply_text


def maybe_extract_note(user_id: int, user_message: str):
    """Very lightweight heuristic memory extraction."""
    lowered = user_message.lower()
    triggers = ["i like", "i love", "i hate", "my name is", "i'm from", "i work", "i study", "my birthday"]
    for t in triggers:
        if t in lowered:
            snippet = user_message.strip()
            if len(snippet) > 140:
                snippet = snippet[:140] + "..."
            db.add_note(user_id, snippet)
            break
