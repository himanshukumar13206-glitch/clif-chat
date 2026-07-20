"""
Handles Nova's personality: builds the system prompt (with per-user memory)
and calls the Anthropic API to generate in-character replies.
"""

import anthropic
from config import ANTHROPIC_API_KEY, BOT_NAME
import database as db

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

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
- Never say you are an AI assistant made by Anthropic; stay in character as {BOT_NAME}. If asked
  directly whether you're an AI, you can be playfully honest without breaking character.
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
        return "(Nova's brain isn't wired up yet — ask my dev to set ANTHROPIC_API_KEY.)"

    history = db.get_chat_history(user_id, limit=20)
    messages = [{"role": h["role"], "content": h["content"]} for h in history]
    messages.append({"role": "user", "content": user_message})

    system_prompt = build_system_prompt(user_id, username)

    response = _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        system=system_prompt,
        messages=messages,
    )
    reply_text = "".join(
        block.text for block in response.content if getattr(block, "type", None) == "text"
    ).strip()

    db.add_chat_message(user_id, "user", user_message)
    db.add_chat_message(user_id, "assistant", reply_text)

    maybe_extract_note(user_id, user_message)

    return reply_text or "..."


def maybe_extract_note(user_id: int, user_message: str):
    """Very lightweight heuristic memory extraction (no extra API call).
    For higher-quality memory, replace this with a small classification call."""
    lowered = user_message.lower()
    triggers = ["i like", "i love", "i hate", "my name is", "i'm from", "i work", "i study", "my birthday"]
    for t in triggers:
        if t in lowered:
            snippet = user_message.strip()
            if len(snippet) > 140:
                snippet = snippet[:140] + "..."
            db.add_note(user_id, snippet)
            break
