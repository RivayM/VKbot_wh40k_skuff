# database/tournament_db.py

from database.db_manager import get_connection
import datetime
import sqlite3

conn, cursor = get_connection()

# Глобальная переменная для расчёта очков
SCORE_RULES = {
    (0, 3): (10, 10),
    (4, 7): (11, 9),
    (8, 11): (12, 8),
    (12, 15): (13, 7),
    (16, 19): (14, 6),
    (20, 23): (15, 5),
    (24, 27): (16, 4),
    (28, 31): (17, 3),
    (32, 35): (18, 2),
    (36, 39): (19, 1),
    (40, 100): (20, 0)
}


def init_tournament_tables():
    """Создаёт таблицы для турнирной системы"""
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tournament_players (
            user_id INTEGER PRIMARY KEY,
            default_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tournament_armies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            army_name TEXT NOT NULL,
            wins INTEGER DEFAULT 0,
            draws INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES tournament_players(user_id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tournaments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            date TEXT,
            status TEXT DEFAULT 'pending',
            max_players INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Добавляем колонку max_players, если её нет
    try:
        cursor.execute('ALTER TABLE tournaments ADD COLUMN max_players INTEGER')
        conn.commit()
    except sqlite3.OperationalError:
        pass
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tournament_registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tournament_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            player_name TEXT,
            army_id INTEGER,
            roster_text TEXT,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (tournament_id) REFERENCES tournaments(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES tournament_players(user_id),
            FOREIGN KEY (army_id) REFERENCES tournament_armies(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tournament_matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tournament_id INTEGER NOT NULL,
            round_number INTEGER NOT NULL,
            registration1_id INTEGER,
            registration2_id INTEGER,
            winner_registration_id INTEGER,
            vp1 INTEGER DEFAULT 0,
            vp2 INTEGER DEFAULT 0,
            to1 INTEGER DEFAULT 0,
            to2 INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (tournament_id) REFERENCES tournaments(id),
            FOREIGN KEY (registration1_id) REFERENCES tournament_registrations(id),
            FOREIGN KEY (registration2_id) REFERENCES tournament_registrations(id),
            FOREIGN KEY (winner_registration_id) REFERENCES tournament_registrations(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tournament_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tournament_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            photo_url TEXT,
            status TEXT DEFAULT 'pending',
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_at TIMESTAMP,
            FOREIGN KEY (tournament_id) REFERENCES tournaments(id),
            FOREIGN KEY (user_id) REFERENCES tournament_players(user_id)
        )
    ''')
    
    # Добавляем колонку player_name, если её нет
    try:
        cursor.execute('ALTER TABLE tournament_registrations ADD COLUMN player_name TEXT')
        conn.commit()
        print("✅ Добавлена колонка player_name")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' not in str(e):
            print(f"⚠️ Не удалось добавить колонку: {e}")
    
    # Добавляем колонку roster_text, если её нет
    try:
        cursor.execute('ALTER TABLE tournament_registrations ADD COLUMN roster_text TEXT')
        conn.commit()
        print("✅ Добавлена колонка roster_text")
    except sqlite3.OperationalError as e:
        if 'duplicate column name' not in str(e):
            print(f"⚠️ Не удалось добавить колонку: {e}")
    
    conn.commit()
    print("✅ Таблицы турниров готовы")


# --- Функции для работы с игроками ---

def get_or_create_player(user_id, default_name=None):
    cursor.execute('SELECT user_id, default_name FROM tournament_players WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    if row:
        return {'user_id': row[0], 'default_name': row[1]}
    if default_name is None:
        default_name = f"player_{user_id}"
    cursor.execute('INSERT INTO tournament_players (user_id, default_name) VALUES (?, ?)', (user_id, default_name))
    conn.commit()
    return {'user_id': user_id, 'default_name': default_name}


def get_player_armies(user_id):
    cursor.execute('SELECT id, army_name, wins, draws, losses FROM tournament_armies WHERE user_id = ?', (user_id,))
    rows = cursor.fetchall()
    return [{'id': r[0], 'army_name': r[1], 'wins': r[2], 'draws': r[3], 'losses': r[4]} for r in rows]


def add_army(user_id, army_name):
    cursor.execute('INSERT INTO tournament_armies (user_id, army_name) VALUES (?, ?)', (user_id, army_name))
    conn.commit()
    return cursor.lastrowid


def update_army_stats(army_id, result):
    if result == 'win':
        cursor.execute('UPDATE tournament_armies SET wins = wins + 1 WHERE id = ?', (army_id,))
    elif result == 'draw':
        cursor.execute('UPDATE tournament_armies SET draws = draws + 1 WHERE id = ?', (army_id,))
    elif result == 'loss':
        cursor.execute('UPDATE tournament_armies SET losses = losses + 1 WHERE id = ?', (army_id,))
    conn.commit()


# --- Функции для турниров ---

def create_tournament(name, date, max_players=None):
    cursor.execute('''
        INSERT INTO tournaments (name, date, max_players, status) VALUES (?, ?, ?, 'pending')
    ''', (name, date, max_players))
    conn.commit()
    return cursor.lastrowid


def get_all_tournaments():
    cursor.execute('SELECT id, name, date, status, max_players FROM tournaments ORDER BY id')
    rows = cursor.fetchall()
    return [{'id': r[0], 'name': r[1], 'date': r[2], 'status': r[3], 'max_players': r[4]} for r in rows]


def get_tournament(tournament_id):
    cursor.execute('SELECT id, name, date, status, max_players FROM tournaments WHERE id = ?', (tournament_id,))
    row = cursor.fetchone()
    if row:
        return {'id': row[0], 'name': row[1], 'date': row[2], 'status': row[3], 'max_players': row[4]}
    return None


def update_tournament(tournament_id, name=None, date=None, max_players=None, status=None):
    updates = []
    params = []
    if name is not None:
        updates.append("name = ?")
        params.append(name)
    if date is not None:
        updates.append("date = ?")
        params.append(date)
    if max_players is not None:
        updates.append("max_players = ?")
        params.append(max_players)
    if status is not None:
        updates.append("status = ?")
        params.append(status)
    if not updates:
        return
    params.append(tournament_id)
    cursor.execute(f"UPDATE tournaments SET {', '.join(updates)} WHERE id = ?", params)
    conn.commit()


def delete_tournament(tournament_id):
    cursor.execute("DELETE FROM tournaments WHERE id = ?", (tournament_id,))
    conn.commit()


# --- Регистрация на турнир ---

def register_for_tournament(tournament_id, user_id, player_name, army_id, roster_text):
    cursor.execute('''
        INSERT INTO tournament_registrations (tournament_id, user_id, player_name, army_id, roster_text)
        VALUES (?, ?, ?, ?, ?)
    ''', (tournament_id, user_id, player_name, army_id, roster_text))
    conn.commit()
    return cursor.lastrowid


def get_registrations(tournament_id):
    cursor.execute('''
        SELECT id, user_id, player_name, roster_text, registered_at
        FROM tournament_registrations
        WHERE tournament_id = ?
        ORDER BY registered_at
    ''', (tournament_id,))
    rows = cursor.fetchall()
    return [{
        'id': r[0],
        'user_id': r[1],
        'player_name': r[2],
        'roster_text': r[3],
        'registered_at': r[4],
        'army_name': None,
        'army_id': None
    } for r in rows]


def get_registration_by_user(tournament_id, user_id):
    cursor.execute('''
        SELECT tr.id, tr.user_id, tr.player_name, tr.roster_text, tr.registered_at,
               ta.army_name, tr.army_id
        FROM tournament_registrations tr
        LEFT JOIN tournament_armies ta ON tr.army_id = ta.id
        WHERE tr.tournament_id = ? AND tr.user_id = ?
    ''', (tournament_id, user_id))
    row = cursor.fetchone()
    if row:
        return {
            'id': row[0],
            'user_id': row[1],
            'player_name': row[2],
            'roster_text': row[3],
            'registered_at': row[4],
            'army_name': row[5],
            'army_id': row[6]
        }
    return None


def is_registered(tournament_id, user_id):
    return get_registration_by_user(tournament_id, user_id) is not None


def get_registration_by_id(reg_id):
    cursor.execute('''
        SELECT tr.id, tr.tournament_id, tr.user_id, tr.player_name, tr.army_id, tr.roster_text, tr.registered_at,
               ta.army_name
        FROM tournament_registrations tr
        LEFT JOIN tournament_armies ta ON tr.army_id = ta.id
        WHERE tr.id = ?
    ''', (reg_id,))
    row = cursor.fetchone()
    if row:
        return {
            'id': row[0], 'tournament_id': row[1], 'user_id': row[2], 'player_name': row[3],
            'army_id': row[4], 'roster_text': row[5], 'registered_at': row[6], 'army_name': row[7]
        }
    return None
# --- Редактирование ---
def update_registration_army(registration_id, army_id):
    cursor.execute('UPDATE tournament_registrations SET army_id = ? WHERE id = ?', (army_id, registration_id))
    conn.commit()


# --- Оплаты ---

def add_payment(tournament_id, user_id, photo_url):
    cursor.execute('''
        INSERT INTO tournament_payments (tournament_id, user_id, photo_url, status)
        VALUES (?, ?, ?, 'pending')
    ''', (tournament_id, user_id, photo_url))
    conn.commit()


# --- Пары и результаты ---

def create_match(tournament_id, round_number, reg1_id, reg2_id=None):
    cursor.execute('''
        INSERT INTO tournament_matches (tournament_id, round_number, registration1_id, registration2_id, status)
        VALUES (?, ?, ?, ?, 'pending')
    ''', (tournament_id, round_number, reg1_id, reg2_id))
    conn.commit()
    return cursor.lastrowid


def get_matches_by_round(tournament_id, round_number):
    cursor.execute('''
        SELECT m.*, 
               r1.player_name as player1_name, r1.user_id as player1_user_id,
               r2.player_name as player2_name, r2.user_id as player2_user_id
        FROM tournament_matches m
        LEFT JOIN tournament_registrations r1 ON m.registration1_id = r1.id
        LEFT JOIN tournament_registrations r2 ON m.registration2_id = r2.id
        WHERE m.tournament_id = ? AND m.round_number = ?
        ORDER BY m.id
    ''', (tournament_id, round_number))
    rows = cursor.fetchall()
    cursor.execute('PRAGMA table_info(tournament_matches)')
    columns = [col[1] for col in cursor.fetchall()]
    result = []
    for row in rows:
        match = {columns[i]: row[i] for i in range(len(columns))}
        match['player1_name'] = row[len(columns)] if len(row) > len(columns) else None
        match['player1_user_id'] = row[len(columns)+1] if len(row) > len(columns)+1 else None
        match['player2_name'] = row[len(columns)+2] if len(row) > len(columns)+2 else None
        match['player2_user_id'] = row[len(columns)+3] if len(row) > len(columns)+3 else None
        result.append(match)
    return result


def get_match(match_id):
    cursor.execute('''
        SELECT m.*, 
               r1.player_name as player1_name, r1.user_id as player1_user_id,
               r2.player_name as player2_name, r2.user_id as player2_user_id
        FROM tournament_matches m
        LEFT JOIN tournament_registrations r1 ON m.registration1_id = r1.id
        LEFT JOIN tournament_registrations r2 ON m.registration2_id = r2.id
        WHERE m.id = ?
    ''', (match_id,))
    row = cursor.fetchone()
    if row:
        cursor.execute('PRAGMA table_info(tournament_matches)')
        columns = [col[1] for col in cursor.fetchall()]
        match = {columns[i]: row[i] for i in range(len(columns))}
        match['player1_name'] = row[len(columns)] if len(row) > len(columns) else None
        match['player1_user_id'] = row[len(columns)+1] if len(row) > len(columns)+1 else None
        match['player2_name'] = row[len(columns)+2] if len(row) > len(columns)+2 else None
        match['player2_user_id'] = row[len(columns)+3] if len(row) > len(columns)+3 else None
        return match
    return None


def update_match_result(match_id, vp1, vp2, winner_reg_id=None):
    diff = abs(vp1 - vp2)
    to_win, to_lose = 10, 10
    for (low, high), (w, l) in SCORE_RULES.items():
        if low <= diff <= high:
            to_win, to_lose = w, l
            break
    if vp1 > vp2:
        to1, to2 = to_win, to_lose
        if winner_reg_id is None:
            winner_reg_id = cursor.execute('SELECT registration1_id FROM tournament_matches WHERE id = ?', (match_id,)).fetchone()[0]
    elif vp2 > vp1:
        to1, to2 = to_lose, to_win
        if winner_reg_id is None:
            winner_reg_id = cursor.execute('SELECT registration2_id FROM tournament_matches WHERE id = ?', (match_id,)).fetchone()[0]
    else:
        to1 = to2 = 10
        winner_reg_id = None

    cursor.execute('''
        UPDATE tournament_matches
        SET vp1 = ?, vp2 = ?, to1 = ?, to2 = ?, winner_registration_id = ?, status = 'completed'
        WHERE id = ?
    ''', (vp1, vp2, to1, to2, winner_reg_id, match_id))
    conn.commit()

    match = get_match(match_id)
    reg1 = get_registration_by_id(match['registration1_id'])
    reg2 = match['registration2_id'] and get_registration_by_id(match['registration2_id'])
    
    if winner_reg_id == match['registration1_id']:
        result1 = 'win'
        result2 = 'loss' if reg2 else None
    elif winner_reg_id == match['registration2_id']:
        result1 = 'loss'
        result2 = 'win'
    else:
        result1 = 'draw'
        result2 = 'draw' if reg2 else None

    if reg1 and reg1['army_id']:
        update_army_stats(reg1['army_id'], result1)
    if reg2 and reg2['army_id'] and result2:
        update_army_stats(reg2['army_id'], result2)


def get_leaderboard(tournament_id):
    cursor.execute('''
        SELECT 
            registration_id,
            SUM(to_points) as total_to,
            SUM(vp_points) as total_vp
        FROM (
            SELECT registration1_id as registration_id, to1 as to_points, vp1 as vp_points FROM tournament_matches WHERE tournament_id = ?
            UNION ALL
            SELECT registration2_id as registration_id, to2 as to_points, vp2 as vp_points FROM tournament_matches WHERE tournament_id = ? AND registration2_id IS NOT NULL
        ) t
        GROUP BY registration_id
    ''', (tournament_id, tournament_id))
    rows = cursor.fetchall()
    result = []
    for reg_id, total_to, total_vp in rows:
        reg = get_registration_by_id(reg_id)
        if reg:
            result.append((reg_id, reg['user_id'], reg['player_name'], total_to or 0, total_vp or 0))
    result.sort(key=lambda x: (x[3], x[4]), reverse=True)
    return result


def update_registration_roster(registration_id, roster_text):
    """Обновляет текст ростера регистрации"""
    cursor.execute('UPDATE tournament_registrations SET roster_text = ? WHERE id = ?', (roster_text, registration_id))
    conn.commit()


def get_pending_payments():
    """Возвращает все ожидающие оплаты"""
    cursor.execute('''
        SELECT tp.id, tp.tournament_id, t.name as tournament_name, tp.user_id, tp.photo_url, tp.submitted_at
        FROM tournament_payments tp
        JOIN tournaments t ON tp.tournament_id = t.id
        WHERE tp.status = 'pending'
    ''')
    rows = cursor.fetchall()
    return [{'id': r[0], 'tournament_id': r[1], 'tournament_name': r[2], 'user_id': r[3], 'photo_url': r[4], 'submitted_at': r[5]} for r in rows]


def approve_payment(payment_id):
    cursor.execute("UPDATE tournament_payments SET status = 'approved', processed_at = CURRENT_TIMESTAMP WHERE id = ?", (payment_id,))
    conn.commit()


def reject_payment(payment_id):
    cursor.execute("UPDATE tournament_payments SET status = 'rejected', processed_at = CURRENT_TIMESTAMP WHERE id = ?", (payment_id,))
    conn.commit()

def delete_registration(registration_id):
    cursor.execute('DELETE FROM tournament_registrations WHERE id = ?', (registration_id,))
    conn.commit()