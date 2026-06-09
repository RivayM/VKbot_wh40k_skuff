# CHAT/user_state.py
import sqlite3
from pathlib import Path

DATA_DIR = Path("/app/data") if Path("/app/data").exists() else Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "chat_users.db"

def get_connection():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_chat_users_table():
    conn = get_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS chat_users (
            user_id INTEGER PRIMARY KEY,
            faction TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ Таблица chat_users готова")

def get_user_data(user_id):
    conn = get_connection()
    row = conn.execute('SELECT faction FROM chat_users WHERE user_id = ?', (user_id,)).fetchone()
    conn.close()
    return {'faction': row['faction']} if row else None

def set_user_faction(user_id, faction):
    conn = get_connection()
    conn.execute('''
        INSERT INTO chat_users (user_id, faction) VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET faction = excluded.faction
    ''', (user_id, faction))
    conn.commit()
    conn.close()