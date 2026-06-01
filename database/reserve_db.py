# database/reserve_db.py
from database.db_manager import get_connection
import datetime

conn, cursor = get_connection()

def init_reserve_table():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reserves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_num INTEGER NOT NULL,
            reserve_date TEXT NOT NULL,
            time_slot INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            user_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(table_num, reserve_date, time_slot)
        )
    ''')
    conn.commit()
    print("✅ Таблица reserves готова")

def clean_old_reserves():
    today = datetime.date.today().isoformat()
    cursor.execute('DELETE FROM reserves WHERE reserve_date < ?', (today,))
    conn.commit()

def is_slot_free(table_num, date_str, time_slot):
    cursor.execute('SELECT 1 FROM reserves WHERE table_num = ? AND reserve_date = ? AND time_slot = ?',
                   (table_num, date_str, time_slot))
    return cursor.fetchone() is None

def create_reserve(table_num, date_str, time_slot, user_id, user_name):
    cursor.execute('''
        INSERT INTO reserves (table_num, reserve_date, time_slot, user_id, user_name)
        VALUES (?, ?, ?, ?, ?)
    ''', (table_num, date_str, time_slot, user_id, user_name))
    conn.commit()
    return True

def get_reserve_info(table_num, date_str, time_slot):
    cursor.execute('SELECT user_id, user_name FROM reserves WHERE table_num = ? AND reserve_date = ? AND time_slot = ?',
                   (table_num, date_str, time_slot))
    row = cursor.fetchone()
    if row:
        return {'user_id': row[0], 'name': row[1]}
    return None

def get_reserves_for_table(table_num):
    cursor.execute('SELECT reserve_date, time_slot, user_name FROM reserves WHERE table_num = ? ORDER BY reserve_date, time_slot',
                   (table_num,))
    return [{'date': r[0], 'slot': r[1], 'name': r[2]} for r in cursor.fetchall()]

def cancel_reserve(table_num, date_str, time_slot):
    cursor.execute('DELETE FROM reserves WHERE table_num = ? AND reserve_date = ? AND time_slot = ?',
                   (table_num, date_str, time_slot))
    conn.commit()
    return cursor.rowcount > 0