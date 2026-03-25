import sqlite3
import os

# Путь к файлу базы данных
DB_PATH = os.path.join(os.path.dirname(__file__), 'sponsors.db')

def get_db():
    """Получить соединение с базой данных"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Создать таблицы при первом запуске"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Таблица спонсоров
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sponsors (
            user_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            registered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_payment_date DATETIME,
            photo_sent_for_period BOOLEAN DEFAULT 0,
            status TEXT DEFAULT 'active'
        )
    ''')
    
    # Таблица платежей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            photo_url TEXT,
            photo_sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            approved BOOLEAN DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES sponsors(user_id)
        )
    ''')
    
    # Таблица настроек (для админа)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ База данных инициализирована")

# ========== ФУНКЦИИ ДЛЯ РАБОТЫ СО СПОНСОРАМИ ==========

def add_sponsor(user_id, name):
    """Добавить нового спонсора"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO sponsors (user_id, name, status) VALUES (?, ?, 'active')",
        (user_id, name)
    )
    conn.commit()
    conn.close()

def get_sponsor(user_id):
    """Получить информацию о спонсоре"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sponsors WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def get_all_sponsors():
    """Получить всех активных спонсоров"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sponsors WHERE status = 'active'")
    results = cursor.fetchall()
    conn.close()
    return results

def remove_sponsor(user_id):
    """Отписать спонсора (меняем статус на inactive)"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE sponsors SET status = 'inactive' WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def set_photo_sent(user_id):
    """Отметить, что спонсор прислал фото за период"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE sponsors SET photo_sent_for_period = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def reset_photo_sent():
    """Сбросить статус фото для нового периода"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE sponsors SET photo_sent_for_period = 0")
    conn.commit()
    conn.close()

def get_sponsors_without_photo():
    """Получить спонсоров, не приславших фото"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM sponsors WHERE status = 'active' AND photo_sent_for_period = 0"
    )
    results = cursor.fetchall()
    conn.close()
    return results

def save_payment_photo(user_id, photo_url):
    """Сохранить фото платежа"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO payments (user_id, photo_url, approved) VALUES (?, ?, 0)",
        (user_id, photo_url)
    )
    conn.commit()
    conn.close()

def get_sponsors_with_photo():
    """Получить спонсоров, приславших фото"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM sponsors WHERE status = 'active' AND photo_sent_for_period = 1"
    )
    results = cursor.fetchall()
    conn.close()
    return results

def get_setting(key, default=None):
    """Получить настройку"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    result = cursor.fetchone()
    conn.close()
    return result['value'] if result else default

def set_setting(key, value):
    """Сохранить настройку"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        (key, value)
    )
    conn.commit()
    conn.close()