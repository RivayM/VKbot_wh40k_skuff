# ==================================================
# БЛОК 1: ИМПОРТ БИБЛИОТЕК И НАСТРОЙКИ
# ==================================================
import vk_api
import os
import logging
from dotenv import load_dotenv
from vk_api.longpoll import VkLongPoll, VkEventType

from database import (
    init_sponsors_table,
    init_key_table,
    is_sponsor,
    add_sponsor,
    remove_sponsor,
    get_all_sponsors,
    get_sponsor,          # <-- ДОБАВИТЬ
    get_sponsor_days,     # <-- ДОБАВИТЬ
    # waiting states
    add_waiting_for_name,
    remove_waiting_for_name,
    is_waiting_for_name,
    add_waiting_for_photo,
    remove_waiting_for_photo,
    is_waiting_for_photo,
    add_waiting_for_unsubscribe,
    remove_waiting_for_unsubscribe,
    is_waiting_for_unsubscribe,
    # key functions
    take_key,
    return_key,
    get_key_holder,
    has_key
)
from database import init_tournaments_table 
from keyboards import get_main_keyboard, get_tournament_keyboard, get_sponsor_keyboard, get_key_keyboard
from utils.helpers import send_message

from handlers.sponsorship import (
    handle_start, handle_sponsor_menu, handle_name_input,
    handle_payment_request, handle_photo_input, handle_unsubscribe,
    handle_unsubscribe_confirm, handle_back,
    is_waiting_for_name as sponsorship_is_waiting_for_name,
    is_waiting_for_photo as sponsorship_is_waiting_for_photo,
    is_waiting_for_unsubscribe as sponsorship_is_waiting_for_unsubscribe
)

from handlers.tournament import (
    handle_tournament_menu, handle_register_for_tournament,
    handle_tournament_selection, handle_start_tournament,
    handle_tournament_name_input, handle_tournament_date_input,
    handle_complete_tournament, handle_tournament_complete_selection,
    handle_list_tournaments, handle_back as tournament_back,
    is_waiting_for_tournament_name, is_waiting_for_tournament_date,
    is_waiting_for_tournament_reg
)

from handlers.key_handler import handle_take_key, handle_return_key, handle_who_has_key
# ==================================================
# БЛОК 2: ЗАГРУЗКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ (ENV)
# ==================================================
load_dotenv()

TOKEN = os.getenv("VK_TOKEN")
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]


# ==================================================
# БЛОК 3: НАСТРОЙКА ЛОГГИРОВАНИЯ
# ==================================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ==================================================
# БЛОК 4: ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ И ПОДКЛЮЧЕНИЕ К ВК
# ==================================================
init_sponsors_table()  # таблицы спонсоров
init_key_table()       # таблица ключей
init_tournaments_table()        # турниры
logger.info("✅ Базы данных инициализированы")

vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkLongPoll(vk_session)

logger.info("🚀 БОТ ЗАПУЩЕН")
logger.info(f"📱 Админы: {ADMIN_IDS}")


# ==================================================
# БЛОК 5: ГЛАВНЫЙ ЦИКЛ ОБРАБОТКИ СООБЩЕНИЙ
# ==================================================

# Словарь для хранения ID последних обработанных сообщений
processed_messages = {}

for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        user_id = event.user_id
        text = event.text.strip() if event.text else ""
        
        if not text:
            continue
        
        # ==============================================
        # ЗАЩИТА ОТ ДУБЛИРОВАНИЯ (улучшенная)
        # ==============================================
        # Используем комбинацию user_id + text + timestamp для уникальности
        import time
        message_key = f"{user_id}_{text}_{int(time.time() / 2)}"  # 2 секунды окно
        
        # Альтернатива: если есть message_id
        message_id = getattr(event, 'message_id', None)
        if message_id:
            message_key = f"{user_id}_{message_id}"
        
        if message_key in processed_messages:
            continue  # Пропускаем дубль
        
        processed_messages[message_key] = True
        
        # Очищаем старые записи (оставляем последние 50)
        if len(processed_messages) > 50:
            # Удаляем самый старый ключ
            oldest_key = next(iter(processed_messages))
            del processed_messages[oldest_key]
        
        # ==============================================
        # БЛОК 6: ПРОВЕРКА СОСТОЯНИЙ ПОЛЬЗОВАТЕЛЯ (ожидание ввода)
        # ==============================================
        
        if is_waiting_for_name(user_id):
            handle_name_input(vk, user_id, text, send_message)
            continue
        
        if is_waiting_for_photo(user_id):
            handle_photo_input(vk, user_id, event.attachments, ADMIN_IDS, send_message)
            continue
        
        if is_waiting_for_unsubscribe(user_id):
            handle_unsubscribe_confirm(vk, user_id, text, send_message)
            continue
        
        if is_waiting_for_tournament_name(user_id):
            handle_tournament_name_input(vk, user_id, text, send_message)
            continue
        
        if is_waiting_for_tournament_date(user_id):
            handle_tournament_date_input(vk, user_id, text, send_message)
            continue
        
        if is_waiting_for_tournament_reg(user_id):
            if handle_tournament_selection(vk, user_id, text, send_message):
                continue
            if handle_tournament_complete_selection(vk, user_id, text, send_message):
                continue
        
        # ==============================================
        # БЛОК 7: ОБРАБОТКА КОМАНД (КНОПОК И ТЕКСТА)
        # ==============================================
        
        # --- ОБРАБОТКА НОВЫХ ПОЛЬЗОВАТЕЛЕЙ (кнопка "Начать") ---
        
        if text == "/start":
            if is_sponsor(user_id):
                days_count = get_sponsor_days(user_id)
                send_message(vk, user_id, 
                    f"🏠 С возвращением!\n\nВы спонсор уже {days_count} дней! 🙏", 
                    get_main_keyboard())
            else:
                send_message(vk, user_id, 
                    "🏠 Добро пожаловать!\n\nЯ бот для управления турнирами, спонсорами и ключами.\n\n"
                    "Выберите раздел в меню ниже:", 
                    get_main_keyboard())
        
        # --- ГЛАВНЫЕ РАЗДЕЛЫ МЕНЮ ---
        
        elif text == "🏆 ТУРНИРЫ":
            send_message(vk, user_id, "🏆 Раздел ТУРНИРЫ\n\nВыберите действие:", get_tournament_keyboard())
        
        elif text == "💰 СПОНСОР":
            send_message(vk, user_id, "💰 Раздел СПОНСОР\n\nВыберите действие:", get_sponsor_keyboard())
        
        elif text == "🔑 КЛЮЧИ":
            send_message(vk, user_id, "🔑 Раздел КЛЮЧИ\n\nВыберите действие:", get_key_keyboard())
        
        # --- КНОПКИ РАЗДЕЛА ТУРНИРЫ ---
        
        elif text == "📝 Зарегистрироваться":
            send_message(vk, user_id, "📝 Функция регистрации на турнир в разработке.\n\nСкоро появится!", get_tournament_keyboard())
        
        elif text == "📊 Сдать результат":
            send_message(vk, user_id, "📊 Функция сдачи результатов в разработке.\n\nСкоро появится!", get_tournament_keyboard())
        
        # --- КНОПКИ РАЗДЕЛА СПОНСОР ---
        
        elif text == "💰 Стать спонсором":
            handle_sponsor_menu(vk, user_id, send_message)
        
        elif text == "✅ Подтвердить оплату":
            handle_payment_request(vk, user_id, send_message)
        
        elif text == "❌ Отписаться":
            handle_unsubscribe(vk, user_id, send_message)
        
        # --- КНОПКИ РАЗДЕЛА КЛЮЧИ ---
        
        elif text == "🔑 Взять ключ":
            handle_take_key(vk, user_id, send_message, ADMIN_IDS)
        
        elif text == "🔓 Отдать ключ":
            handle_return_key(vk, user_id, send_message, ADMIN_IDS)
        
        elif text == "❓ Кто держит ключ":
            handle_who_has_key(vk, user_id, send_message)
        
        # --- КНОПКА НАЗАД ---
        
        elif text == "🔙 Назад":
            from handlers.sponsorship import handle_cancel_photo
            if handle_cancel_photo(vk, user_id, send_message):
                continue
            if is_sponsor(user_id):
                days_count = get_sponsor_days(user_id)
                send_message(vk, user_id, 
                    f"🏠 Главное меню\n\nВы спонсор уже {days_count} дней! 🙏", 
                    get_main_keyboard())
            else:
                send_message(vk, user_id, "🏠 Главное меню:", get_main_keyboard())
        
        # --- НЕИЗВЕСТНАЯ КОМАНДА ---
        
        else:
            send_message(vk, user_id, "❓ Неизвестная команда.\n\nНажмите /start или кнопку 'Начать' для начала работы.")