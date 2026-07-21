"""
Handles Nova's personality: builds the system prompt (with per-user memory)
and calls the Google Gemini API (new google-genai SDK).
"""

import traceback
print("Loading persona module...")

from google import genai
from google.genai import types
from config import BOT_NAME, GEMINI_API_KEY
import database as db

print(f"GEMINI_API_KEY present: {bool(GEMINI_API_KEY)}")

_client = None
if GEMINI_API_KEY:
    try:
        _client = genai.Client(api_key=GEMINI_API_KEY)
        print("Gemini client initialized successfully.")
    except Exception as e:
        print(f"Failed to init Gemini client: {e}")
else:
    print("WARNING: GEMINI_API_KEY is not set.")

BASE_SYSTEM_PROMPT = f"""You are {BOT_NAME}, a Telegram bot with a warm, witty, flirty personality.
...  (same system prompt as before) ...
"""

def build_system_prompt(user_id: int, username: str) -> str:
    # ... unchanged ...
    pass

def chat_reply(user_id: int, username: str, user_message: str) -> str:
    print("chat_reply called")  # will appear in logs when a message arrives
    if _client is None:
        return "(Nova's brain isn't wired up yet — ask my dev to set GEMINI_API_KEY.)"

    system_prompt = build_system_prompt(user_id, username)
    history = db.get_chat_history(user_id, limit=20)
    contents = []
    for h in history:
        role = "user" if h["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part(text=h["content"])]))
    contents.append(types.Content(role="user", parts=[types.Part(text=user_message)]))

    try:
        response = _client.models.generate_content(
            model="gemini-2.0-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=300,
                temperature=0.9,
            ),
        )
        reply_text = response.text.strip()
    except Exception as e:
        print("=== Gemini API Error ===")
        traceback.print_exc()
        reply_text = "🤖 Nova can't think right now (API error). Try again later."

    db.add_chat_message(user_id, "user", user_message)
    db.add_chat_message(user_id, "assistant", reply_text)
    maybe_extract_note(user_id, user_message)
    return reply_text

def maybe_extract_note(user_id, user_message):
    # ... unchanged ...
    pass
