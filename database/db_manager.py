import sqlite3
import logging

logger = logging.getLogger(__name__)

# Глобальные переменные для подключения
conn = None
cursor = None


def get_connection():
    """Возвращает соединение с БД"""
    global conn, cursor
    if conn is None:
        conn = sqlite3.connect('bot_database.db', check_same_thread=False)
        cursor = conn.cursor()
        logger.info("✅ Подключение к БД установлено")
    return conn, cursor


def close_connection():
    """Закрывает соединение с БД"""
    global conn, cursor
    if conn:
        conn.close()
        conn = None
        cursor = None
        logger.info("🔌 Подключение к БД закрыто")