# database/sponsors_db.py
from database.db_manager import get_connection
import datetime

conn, cursor = get_connection()

# Московское время (UTC+3)
MOSCOW_TZ = datetime.timezone(datetime.timedelta(hours=3))

def get_moscow_now():
    """Возвращает текущее московское время как строку"""
    return datetime.datetime.now(MOSCOW_TZ).strftime('%Y-%m-%d %H:%M:%S')


def init_sponsors_table():
    """Создаёт таблицы для спонсоров"""
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sponsors (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Добавляем колонку last_payment если её нет
    try:
        cursor.execute('ALTER TABLE sponsors ADD COLUMN last_payment TIMESTAMP')
        conn.commit()
    except:
        pass
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS waiting_for_name (
            user_id INTEGER PRIMARY KEY
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS waiting_for_photo (
            user_id INTEGER PRIMARY KEY
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS waiting_for_unsubscribe (
            user_id INTEGER PRIMARY KEY
        )
    ''')
    
    conn.commit()
    print("✅ Таблицы спонсоров готовы")


def is_sponsor(user_id):
    cursor.execute('SELECT 1 FROM sponsors WHERE user_id = ?', (user_id,))
    return cursor.fetchone() is not None


def add_sponsor(user_id, name):
    cursor.execute('INSERT OR IGNORE INTO sponsors (user_id, name) VALUES (?, ?)', (user_id, name))
    conn.commit()


def remove_sponsor(user_id):
    cursor.execute('DELETE FROM sponsors WHERE user_id = ?', (user_id,))
    conn.commit()


def get_sponsor(user_id):
    cursor.execute('SELECT user_id, name, registered_at, last_payment FROM sponsors WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    if row:
        return {'user_id': row[0], 'name': row[1], 'registered_at': row[2], 'last_payment': row[3]}
    return None

def get_all_sponsors():
    cursor.execute('SELECT user_id, name, registered_at, last_payment FROM sponsors')
    rows = cursor.fetchall()
    return [{'user_id': r[0], 'name': r[1], 'registered_at': r[2], 'last_payment': r[3]} for r in rows]


def get_sponsor_days(user_id):
    cursor.execute('SELECT registered_at FROM sponsors WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    if result:
        reg_date_str = result[0]
        try:
            reg_date = datetime.datetime.strptime(reg_date_str, '%Y-%m-%d %H:%M:%S')
        except:
            reg_date = datetime.datetime.strptime(reg_date_str, '%Y-%m-%d')
        days = (datetime.datetime.now() - reg_date).days
        return days
    return 0


def update_payment_date(user_id):
    """Обновляет дату последнего платежа спонсора"""
    cursor.execute('''
        UPDATE sponsors 
        SET last_payment = CURRENT_TIMESTAMP 
        WHERE user_id = ?
    ''', (user_id,))
    conn.commit()


# ========== WAITING STATES ==========

def add_waiting_for_name(user_id):
    cursor.execute('INSERT OR IGNORE INTO waiting_for_name (user_id) VALUES (?)', (user_id,))
    conn.commit()


def remove_waiting_for_name(user_id):
    cursor.execute('DELETE FROM waiting_for_name WHERE user_id = ?', (user_id,))
    conn.commit()


def is_waiting_for_name(user_id):
    cursor.execute('SELECT 1 FROM waiting_for_name WHERE user_id = ?', (user_id,))
    return cursor.fetchone() is not None


def add_waiting_for_photo(user_id):
    cursor.execute('INSERT OR IGNORE INTO waiting_for_photo (user_id) VALUES (?)', (user_id,))
    conn.commit()


def remove_waiting_for_photo(user_id):
    cursor.execute('DELETE FROM waiting_for_photo WHERE user_id = ?', (user_id,))
    conn.commit()


def is_waiting_for_photo(user_id):
    cursor.execute('SELECT 1 FROM waiting_for_photo WHERE user_id = ?', (user_id,))
    return cursor.fetchone() is not None


def add_waiting_for_unsubscribe(user_id):
    cursor.execute('INSERT OR IGNORE INTO waiting_for_unsubscribe (user_id) VALUES (?)', (user_id,))
    conn.commit()


def remove_waiting_for_unsubscribe(user_id):
    cursor.execute('DELETE FROM waiting_for_unsubscribe WHERE user_id = ?', (user_id,))
    conn.commit()


def is_waiting_for_unsubscribe(user_id):
    cursor.execute('SELECT 1 FROM waiting_for_unsubscribe WHERE user_id = ?', (user_id,))
    return cursor.fetchone() is not None