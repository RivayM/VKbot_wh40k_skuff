from database.db_manager import get_connection

conn, cursor = get_connection()


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
        
        cursor.execute('''
            UPDATE key_holder 
            SET user_id = ?, user_name = ?, taken_at = CURRENT_TIMESTAMP 
            WHERE id = 1
        ''', (user_id, user_name))
        conn.commit()
        return (old_id, old_name)
    else:
        cursor.execute('INSERT INTO key_holder (id, user_id, user_name) VALUES (1, ?, ?)', 
                       (user_id, user_name))
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
