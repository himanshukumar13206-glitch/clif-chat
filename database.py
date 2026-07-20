import sqlite3
import time
import os
from contextlib import contextmanager

from config import DB_PATH

os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)


def _connect():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


_conn = _connect()


@contextmanager
def cursor():
    cur = _conn.cursor()
    try:
        yield cur
        _conn.commit()
    finally:
        cur.close()


def init_db():
    with cursor() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance INTEGER DEFAULT 500,
            xp INTEGER DEFAULT 0,
            last_daily REAL DEFAULT 0,
            protected_until REAL DEFAULT 0,
            married_to INTEGER DEFAULT NULL,
            alive INTEGER DEFAULT 1,
            kills INTEGER DEFAULT 0,
            bet_count_today INTEGER DEFAULT 0,
            bet_day REAL DEFAULT 0
        )""")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS sudo (
            user_id INTEGER PRIMARY KEY
        )""")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS authorized_chats (
            chat_id INTEGER PRIMARY KEY
        )""")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            role TEXT,
            content TEXT,
            ts REAL
        )""")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS user_notes (
            user_id INTEGER,
            note TEXT,
            ts REAL
        )""")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS group_settings (
            chat_id INTEGER PRIMARY KEY,
            groupbot_on INTEGER DEFAULT 1,
            groupmode TEXT DEFAULT 'normal'
        )""")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS user_prefs (
            user_id INTEGER PRIMARY KEY,
            checkins INTEGER DEFAULT 1,
            reactions INTEGER DEFAULT 1,
            personal_mode TEXT DEFAULT 'normal'
        )""")


# ---------- Users ----------

def get_or_create_user(user_id: int, username: str = ""):
    with cursor() as cur:
        cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        row = cur.fetchone()
        if row is None:
            cur.execute(
                "INSERT INTO users (user_id, username, balance) VALUES (?,?,500)",
                (user_id, username),
            )
            cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
            row = cur.fetchone()
        elif username and row["username"] != username:
            cur.execute("UPDATE users SET username=? WHERE user_id=?", (username, user_id))
        return dict(row)


def get_user(user_id: int):
    with cursor() as cur:
        cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def update_balance(user_id: int, delta: int):
    with cursor() as cur:
        cur.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (delta, user_id))
        cur.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        return cur.fetchone()["balance"]


def set_balance(user_id: int, amount: int):
    with cursor() as cur:
        cur.execute("UPDATE users SET balance=? WHERE user_id=?", (amount, user_id))


def add_xp(user_id: int, amount: int):
    with cursor() as cur:
        cur.execute("UPDATE users SET xp = xp + ? WHERE user_id=?", (amount, user_id))


def top_rich(limit: int = 10):
    with cursor() as cur:
        cur.execute("SELECT user_id, username, balance FROM users ORDER BY balance DESC LIMIT ?", (limit,))
        return [dict(r) for r in cur.fetchall()]


def top_xp(limit: int = 10):
    with cursor() as cur:
        cur.execute("SELECT user_id, username, xp FROM users ORDER BY xp DESC LIMIT ?", (limit,))
        return [dict(r) for r in cur.fetchall()]


def top_killers(limit: int = 10):
    with cursor() as cur:
        cur.execute("SELECT user_id, username, kills FROM users ORDER BY kills DESC LIMIT ?", (limit,))
        return [dict(r) for r in cur.fetchall()]


def get_rank(user_id: int):
    with cursor() as cur:
        cur.execute("SELECT user_id FROM users ORDER BY xp DESC")
        rows = [r["user_id"] for r in cur.fetchall()]
        try:
            return rows.index(user_id) + 1, len(rows)
        except ValueError:
            return None, len(rows)


def set_daily_claim(user_id: int, ts: float):
    with cursor() as cur:
        cur.execute("UPDATE users SET last_daily=? WHERE user_id=?", (ts, user_id))


def set_protection(user_id: int, until_ts: float):
    with cursor() as cur:
        cur.execute("UPDATE users SET protected_until=? WHERE user_id=?", (until_ts, user_id))


def is_protected(user_id: int) -> bool:
    user = get_user(user_id)
    return bool(user and user["protected_until"] > time.time())


def set_alive(user_id: int, alive: bool):
    with cursor() as cur:
        cur.execute("UPDATE users SET alive=? WHERE user_id=?", (1 if alive else 0, user_id))


def increment_kills(user_id: int):
    with cursor() as cur:
        cur.execute("UPDATE users SET kills = kills + 1 WHERE user_id=?", (user_id,))


def set_marriage(user_id: int, partner_id):
    with cursor() as cur:
        cur.execute("UPDATE users SET married_to=? WHERE user_id=?", (partner_id, user_id))


# ---------- Sudo ----------

def add_sudo(user_id: int):
    with cursor() as cur:
        cur.execute("INSERT OR IGNORE INTO sudo (user_id) VALUES (?)", (user_id,))


def del_sudo(user_id: int):
    with cursor() as cur:
        cur.execute("DELETE FROM sudo WHERE user_id=?", (user_id,))


def is_sudo(user_id: int) -> bool:
    with cursor() as cur:
        cur.execute("SELECT 1 FROM sudo WHERE user_id=?", (user_id,))
        return cur.fetchone() is not None


def list_sudo():
    with cursor() as cur:
        cur.execute("SELECT user_id FROM sudo")
        return [r["user_id"] for r in cur.fetchall()]


# ---------- Authorized chats ----------

def add_auth_chat(chat_id: int):
    with cursor() as cur:
        cur.execute("INSERT OR IGNORE INTO authorized_chats (chat_id) VALUES (?)", (chat_id,))


def del_auth_chat(chat_id: int):
    with cursor() as cur:
        cur.execute("DELETE FROM authorized_chats WHERE chat_id=?", (chat_id,))


def is_auth_chat(chat_id: int) -> bool:
    with cursor() as cur:
        cur.execute("SELECT 1 FROM authorized_chats WHERE chat_id=?", (chat_id,))
        return cur.fetchone() is not None


def list_auth_chats():
    with cursor() as cur:
        cur.execute("SELECT chat_id FROM authorized_chats")
        return [r["chat_id"] for r in cur.fetchall()]


# ---------- Chat memory ----------

def add_chat_message(user_id: int, role: str, content: str):
    with cursor() as cur:
        cur.execute(
            "INSERT INTO chat_history (user_id, role, content, ts) VALUES (?,?,?,?)",
            (user_id, role, content, time.time()),
        )
        # keep only last 20 messages per user
        cur.execute("""
            DELETE FROM chat_history WHERE id IN (
                SELECT id FROM chat_history WHERE user_id=?
                ORDER BY id DESC LIMIT -1 OFFSET 20
            )""", (user_id,))


def get_chat_history(user_id: int, limit: int = 20):
    with cursor() as cur:
        cur.execute(
            "SELECT role, content FROM chat_history WHERE user_id=? ORDER BY id ASC LIMIT ?",
            (user_id, limit),
        )
        return [dict(r) for r in cur.fetchall()]


def add_note(user_id: int, note: str):
    with cursor() as cur:
        cur.execute("INSERT INTO user_notes (user_id, note, ts) VALUES (?,?,?)", (user_id, note, time.time()))
        cur.execute("""
            DELETE FROM user_notes WHERE rowid NOT IN (
                SELECT rowid FROM user_notes WHERE user_id=? ORDER BY ts DESC LIMIT 15
            ) AND user_id=?""", (user_id, user_id))


def get_notes(user_id: int):
    with cursor() as cur:
        cur.execute("SELECT note FROM user_notes WHERE user_id=? ORDER BY ts DESC LIMIT 15", (user_id,))
        return [r["note"] for r in cur.fetchall()]


# ---------- Group settings ----------

def get_group_settings(chat_id: int):
    with cursor() as cur:
        cur.execute("SELECT * FROM group_settings WHERE chat_id=?", (chat_id,))
        row = cur.fetchone()
        if row is None:
            cur.execute("INSERT INTO group_settings (chat_id) VALUES (?)", (chat_id,))
            cur.execute("SELECT * FROM group_settings WHERE chat_id=?", (chat_id,))
            row = cur.fetchone()
        return dict(row)


def set_groupbot(chat_id: int, on: bool):
    get_group_settings(chat_id)
    with cursor() as cur:
        cur.execute("UPDATE group_settings SET groupbot_on=? WHERE chat_id=?", (1 if on else 0, chat_id))


def set_groupmode(chat_id: int, mode: str):
    get_group_settings(chat_id)
    with cursor() as cur:
        cur.execute("UPDATE group_settings SET groupmode=? WHERE chat_id=?", (mode, chat_id))


# ---------- Per-user prefs (quiet/chatty, checkins, reactions) ----------

def get_prefs(user_id: int):
    with cursor() as cur:
        cur.execute("SELECT * FROM user_prefs WHERE user_id=?", (user_id,))
        row = cur.fetchone()
        if row is None:
            cur.execute("INSERT INTO user_prefs (user_id) VALUES (?)", (user_id,))
            cur.execute("SELECT * FROM user_prefs WHERE user_id=?", (user_id,))
            row = cur.fetchone()
        return dict(row)


def set_pref(user_id: int, field: str, value):
    get_prefs(user_id)
    with cursor() as cur:
        cur.execute(f"UPDATE user_prefs SET {field}=? WHERE user_id=?", (value, user_id))
