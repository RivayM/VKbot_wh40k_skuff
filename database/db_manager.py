
import logging

import os
import sqlite3

logger = logging.getLogger(__name__)

# Глобальные переменные для подключения
conn = None
cursor = None

# Папка для постоянного хранения (на Bothost это /app/data)
DATA_DIR = '/app/data' if os.path.exists('/app/data') else 'data'
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, 'bot_database.db')

def get_connection():
    global conn, cursor
    if conn is None:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        cursor = conn.cursor()
        logger.info(f"✅ Подключение к БД установлено: {DB_PATH}")
    return conn, cursor


def close_connection():
    """Закрывает соединение с БД"""
    global conn, cursor
    if conn:
        conn.close()
        conn = None
        cursor = None
        logger.info("🔌 Подключение к БД закрыто")