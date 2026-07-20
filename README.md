# Nova — Telegram Companion Bot

A persona-driven Telegram bot with AI chat + memory, a virtual economy, PvP actions,
romance mechanics, admin tools, and a couple of fully working games — plus a clean
pattern for adding more games.

## What's fully built

- `/start` and full button-based Help menu (exactly as spec'd)
- AI persona chat (Nova) powered by the Anthropic API, with per-user rolling memory
  and lightweight "remembers what you told me" notes
- Group behavior: replies on @mention/name/reply, otherwise chimes in occasionally;
  `/quiet` `/chatty` per-user, `/groupbot` `/groupmode` for admins
- Full virtual economy: `/balance`, `/daily`, `/give`, `/toprich`, `/rank`
- Actions: `/rob`, `/kill`, `/protect`, `/shield`, `/revive`, `/topkill`
- Romance: `/propose`, `/divorce`, `/marriage`, `/couple`
- Admin: `/addsudo`, `/delsudo`, `/sudolist`, `/auth`, `/unauth`, `/authlist`
- Games: `/bet` (+ plain-text `bbet` shorthand, daily limit built in) and `/rps`
  (full multiplayer lobby + DM move picking + payout)

## Honest scope note

You asked for 15+ games (UNO, Mines, Wordgrid, Chess with ELO, Hack, Cards, etc).
Building all of those properly — image generation for Wordgrid, a real chess engine
and ELO system, inline mini-apps for UNO/Mines — is realistically 10-15 separate
mini-projects, not something to bolt on safely in one pass. This bot ships with a
clean, consistent pattern (see `games/bet.py` and `games/rps.py`) so each additional
game can be added the same way, one at a time, without destabilizing the rest of the
bot. Happy to build the next one with you whenever you're ready — tell me which game
matters most and we'll do that one next.

Also worth knowing: `/couple` currently ships between group **admins** because Telegram
bots can't fetch a full member list — for a true "any two active chatters" version,
the bot needs to track recent senders per group, which is a small addition I can add.

## Local setup

1. Install Python 3.11+.
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in:
   - `BOT_TOKEN` — from [@BotFather](https://t.me/BotFather) (`/newbot`)
   - `ANTHROPIC_API_KEY` — from the Anthropic Console
   - `OWNER_ID` — your numeric Telegram user ID (get it from [@userinfobot](https://t.me/userinfobot))
4. Export those variables into your shell (or use `python-dotenv` / your own loader),
   then run:
   ```bash
   python main.py
   ```

## File structure

```
novabot/
├── main.py              # entrypoint, registers all handlers
├── config.py             # env var config
├── database.py            # SQLite persistence layer
├── persona.py             # Nova's personality + Anthropic API calls
├── keyboards.py            # inline keyboard layouts
├── handlers/
│   ├── start.py            # /start + help menu text/buttons
│   ├── economy.py           # balance/daily/give/toprich/rank
│   ├── actions.py            # rob/kill/protect/shield/revive/topkill
│   ├── romance.py             # propose/divorce/marriage/couple
│   ├── admin.py                # sudo/auth/groupbot/groupmode
│   └── chat_ai.py               # AI chat + quiet/chatty/checkins/reactions
├── games/
│   ├── bet.py                    # solo double-or-nothing
│   └── rps.py                     # multiplayer RPS betting arena
├── requirements.txt
├── render.yaml
└── .env.example
```

## Deploying on Render

This bot uses long-polling (`run_polling`), so it should be deployed as a **Background
Worker**, not a Web Service (workers don't need to bind to a port).

### Option A — using the Render dashboard

1. Push this project to a GitHub repo.
2. In Render, click **New +** → **Background Worker**.
3. Connect your GitHub repo.
4. Set:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
5. Under **Environment**, add:
   - `BOT_TOKEN`
   - `ANTHROPIC_API_KEY`
   - `OWNER_ID`
   - `BOT_NAME` (optional, defaults to `Nova`)
6. Click **Create Background Worker**. Render will build and start it; check the
   **Logs** tab for `Nova is starting...`.

### Option B — using the included `render.yaml` (Blueprint)

1. Push this project (including `render.yaml`) to a GitHub repo.
2. In Render, click **New +** → **Blueprint**, and point it at your repo.
3. Render reads `render.yaml` and creates the worker automatically — you'll just be
   prompted to fill in the secret env vars (`BOT_TOKEN`, `ANTHROPIC_API_KEY`, `OWNER_ID`).
4. Deploy.

### Notes on Render specifically

- **Persistence**: the bot uses a local SQLite file (`data/nova.db`). Render's disks
  on Background Workers are ephemeral by default — data will reset on redeploys. For
  production, either add a paid **Render Disk** mounted at `data/` (Render dashboard →
  your service → **Disks**) or migrate `database.py` to a hosted Postgres instance
  later on. For testing/early launch, the ephemeral disk is fine.
- Only run **one instance** of this bot at a time (don't set instance count > 1) —
  Telegram's long-polling API only allows one active `getUpdates` connection per bot
  token.
