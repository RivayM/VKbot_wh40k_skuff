# database/tournaments_db.py

from database.db_manager import get_connection
import datetime

conn, cursor = get_connection()


def init_tournaments_table():
    """Создаёт таблицы для турниров"""
    
    # Таблица турниров
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tournaments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            date TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Таблица регистрации участников
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tournament_registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tournament_id INTEGER,
            user_id INTEGER,
            user_name TEXT,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tournament_id) REFERENCES tournaments(id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    print("✅ Таблицы турниров готовы")


def create_tournament(name, date):
    """Создаёт новый турнир"""
    cursor.execute('''
        INSERT INTO tournaments (name, date, status) VALUES (?, ?, 'pending')
    ''', (name, date))
    conn.commit()
    return cursor.lastrowid


def get_active_tournaments():
    """Возвращает активные (не завершённые) турниры"""
    cursor.execute('''
        SELECT id, name, date, status FROM tournaments 
        WHERE status != 'completed'
        ORDER BY created_at DESC
    ''')
    return cursor.fetchall()


def get_all_tournaments():
    """Возвращает все турниры"""
    cursor.execute('SELECT id, name, date, status FROM tournaments ORDER BY created_at DESC')
    return cursor.fetchall()


def get_tournament(tournament_id):
    """Возвращает информацию о турнире по ID"""
    cursor.execute('SELECT id, name, date, status FROM tournaments WHERE id = ?', (tournament_id,))
    return cursor.fetchone()


def register_for_tournament(tournament_id, user_id, user_name):
    """Регистрирует пользователя на турнир"""
    # Проверяем, не зарегистрирован ли уже
    cursor.execute('''
        SELECT 1 FROM tournament_registrations 
        WHERE tournament_id = ? AND user_id = ?
    ''', (tournament_id, user_id))
    
    if cursor.fetchone():
        return False  # Уже зарегистрирован
    
    cursor.execute('''
        INSERT INTO tournament_registrations (tournament_id, user_id, user_name)
        VALUES (?, ?, ?)
    ''', (tournament_id, user_id, user_name))
    conn.commit()
    return True


def get_tournament_registrations(tournament_id):
    """Возвращает список участников турнира"""
    cursor.execute('''
        SELECT user_id, user_name, registered_at 
        FROM tournament_registrations 
        WHERE tournament_id = ?
    ''', (tournament_id,))
    return cursor.fetchall()


def is_registered_for_tournament(tournament_id, user_id):
    """Проверяет, зарегистрирован ли пользователь на турнир"""
    cursor.execute('''
        SELECT 1 FROM tournament_registrations 
        WHERE tournament_id = ? AND user_id = ?
    ''', (tournament_id, user_id))
    return cursor.fetchone() is not None


def start_tournament(tournament_id):
    """Начинает турнир"""
    cursor.execute('''
        UPDATE tournaments SET status = 'active' WHERE id = ?
    ''', (tournament_id,))
    conn.commit()


def complete_tournament(tournament_id):
    """Завершает турнир"""
    cursor.execute('''
        UPDATE tournaments SET status = 'completed' WHERE id = ?
    ''', (tournament_id,))
    conn.commit()


def get_active_tournament():
    """Возвращает активный (текущий) турнир"""
    cursor.execute('''
        SELECT id, name, date, status FROM tournaments 
        WHERE status = 'active'
        LIMIT 1
    ''')
    return cursor.fetchone()