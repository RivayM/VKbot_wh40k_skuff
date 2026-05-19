# database/events_db.py
from database.db_manager import get_connection
import datetime
import logging

logger = logging.getLogger(__name__)

conn, cursor = get_connection()

def init_events_table():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            creator_id INTEGER NOT NULL,
            event_date TEXT NOT NULL,
            delete_after TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS event_participants (
            event_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            user_name TEXT NOT NULL,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (event_id, user_id),
            FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    logger.info("✅ Таблицы мероприятий инициализированы")

def add_event(name, creator_id, event_date):
    delete_after = (event_date + datetime.timedelta(days=2)).strftime('%Y-%m-%d')
    cursor.execute('''
        INSERT INTO events (name, creator_id, event_date, delete_after)
        VALUES (?, ?, ?, ?)
    ''', (name, creator_id, event_date.strftime('%Y-%m-%d'), delete_after))
    conn.commit()
    return cursor.lastrowid

def get_all_events():
    now = datetime.datetime.now().date()
    cursor.execute('DELETE FROM events WHERE delete_after < ?', (now.strftime('%Y-%m-%d'),))
    conn.commit()
    cursor.execute('SELECT id, name, event_date FROM events ORDER BY id')
    rows = cursor.fetchall()
    return [{'id': r[0], 'name': r[1], 'event_date': r[2]} for r in rows]

def delete_event(event_id):
    cursor.execute('DELETE FROM events WHERE id = ?', (event_id,))
    conn.commit()
    return cursor.rowcount > 0

def add_participant(event_id, user_id, user_name):
    cursor.execute('''
        INSERT OR IGNORE INTO event_participants (event_id, user_id, user_name)
        VALUES (?, ?, ?)
    ''', (event_id, user_id, user_name))
    conn.commit()
    return cursor.rowcount > 0

def remove_participant(event_id, user_id):
    cursor.execute('DELETE FROM event_participants WHERE event_id = ? AND user_id = ?', (event_id, user_id))
    conn.commit()
    return cursor.rowcount > 0

def get_participants(event_id):
    cursor.execute('SELECT user_id, user_name FROM event_participants WHERE event_id = ? ORDER BY registered_at', (event_id,))
    rows = cursor.fetchall()
    return [{'user_id': r[0], 'name': r[1]} for r in rows]

def is_participant(event_id, user_id):
    cursor.execute('SELECT 1 FROM event_participants WHERE event_id = ? AND user_id = ?', (event_id, user_id))
    return cursor.fetchone() is not None