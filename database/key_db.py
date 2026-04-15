# database/key_db.py

from database.db_manager import get_connection
import datetime

conn, cursor = get_connection()

# Московское время (UTC+3)
MOSCOW_TZ = datetime.timezone(datetime.timedelta(hours=3))

def get_moscow_now():
    """Возвращает текущее московское время как строку"""
    return datetime.datetime.now(MOSCOW_TZ).strftime('%Y-%m-%d %H:%M:%S')


def init_key_table():
    """Создаёт таблицу для ключей"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS key_holder (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            user_id INTEGER NOT NULL,
            user_name TEXT,
            taken_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    print("✅ Таблица key_holder готова")


def take_key(user_id, user_name):
    """
    Забрать ключ
    Возвращает:
    - True если ключ был свободен
    - (old_id, old_name) если перехват
    - None если ключ уже у этого пользователя
    """
    cursor.execute('SELECT user_id, user_name FROM key_holder WHERE id = 1')
    current = cursor.fetchone()
    
    if current:
        old_id, old_name = current
        if old_id == user_id:
            return None
        
        moscow_now = get_moscow_now()
        cursor.execute('''
            UPDATE key_holder 
            SET user_id = ?, user_name = ?, taken_at = ?
            WHERE id = 1
        ''', (user_id, user_name, moscow_now))
        conn.commit()
        return (old_id, old_name)
    else:
        moscow_now = get_moscow_now()
        cursor.execute('''
            INSERT INTO key_holder (id, user_id, user_name, taken_at) VALUES (1, ?, ?, ?)
        ''', (user_id, user_name, moscow_now))
        conn.commit()
        return True


def return_key():
    """Отдать ключ (освободить)"""
    cursor.execute('DELETE FROM key_holder WHERE id = 1')
    conn.commit()


def get_key_holder():
    """Кто сейчас держит ключ"""
    cursor.execute('SELECT user_id, user_name FROM key_holder WHERE id = 1')
    return cursor.fetchone()


def has_key(user_id):
    """Есть ли ключ у этого пользователя"""
    cursor.execute('SELECT 1 FROM key_holder WHERE id = 1 AND user_id = ?', (user_id,))
    return cursor.fetchone() is not None