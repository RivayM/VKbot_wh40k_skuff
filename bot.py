# ==================================================
# БЛОК 1: ИМПОРТ БИБЛИОТЕК И НАСТРОЙКИ
# ==================================================
# ==================================================
# БЛОК 1: ИМПОРТ БИБЛИОТЕК И НАСТРОЙКИ
# ==================================================
import vk_api
import os
import logging
from dotenv import load_dotenv
from vk_api.longpoll import VkLongPoll, VkEventType

# Модули обработчиков
from handlers.tournament_user import *          # всё из турниров
from handlers.key_handler import handle_take_key, handle_return_key, handle_who_has_key
from handlers.sponsorship import *  

# Клавиатуры
from keyboards import *  

# Утилиты
from utils.helpers import send_message, extract_photo_url

# Инициализация таблиц
from database.tournament_db import init_tournament_tables

# Общие функции базы данных
# Общие функции базы данных
from database import (
    init_sponsors_table,
    init_key_table,
    is_sponsor,
    add_sponsor,
    remove_sponsor,
    get_all_sponsors,
    get_sponsor,
    get_sponsor_days,
    take_key,
    return_key,
    get_key_holder,
    has_key
)
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
init_tournament_tables()  # турниры
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
        # ОБРАБОТКА КНОПКИ «НАЗАД» (сброс любых ожиданий)
        # ==============================================
        if text == "🔙 Назад":
            # Очищаем все возможные состояния ожидания
            if user_id in waiting_for_tournament_choice:
                del waiting_for_tournament_choice[user_id]
            if user_id in waiting_for_registration_name:
                del waiting_for_registration_name[user_id]
            if user_id in waiting_for_registration_army:
                del waiting_for_registration_army[user_id]
            if user_id in waiting_for_registration_roster:
                del waiting_for_registration_roster[user_id]
            if user_id in waiting_for_payment_photo:
                del waiting_for_payment_photo[user_id]
            if user_id in waiting_for_match_result:
                del waiting_for_match_result[user_id]
            if user_id in waiting_for_new_tournament_name:
                del waiting_for_new_tournament_name[user_id]
            if user_id in waiting_for_new_tournament_date:
                del waiting_for_new_tournament_date[user_id]
            if user_id in waiting_for_new_tournament_max_players:
                del waiting_for_new_tournament_max_players[user_id]
            if user_id in waiting_for_reset_confirm:
                del waiting_for_reset_confirm[user_id]
            if user_id in waiting_for_edit_army:
                del waiting_for_edit_army[user_id]
            if user_id in waiting_for_edit_choice:
                del waiting_for_edit_choice[user_id]
            if user_id in waiting_for_edit_roster:
                del waiting_for_edit_roster[user_id]
            is_admin = user_id in ADMIN_IDS
            if handle_cancel_payment(vk, user_id, send_message, is_admin):
                continue

            # Возвращаемся в предыдущее меню
            if user_id in selected_tournament:
                # Был выбран турнир → показываем список турниров
                del selected_tournament[user_id]
                is_admin = user_id in ADMIN_IDS
                handle_list_tournaments_user(vk, user_id, send_message, is_admin)
            else:
                # Нет выбранного турнира → главное меню
                if is_sponsor(user_id):
                    days_count = get_sponsor_days(user_id)
                    send_message(vk, user_id,
                        f"🏠 Главное меню\n\nВы спонсор уже {days_count} дней! 🙏",
                        get_main_keyboard())
                else:
                    send_message(vk, user_id, "🏠 Главное меню:", get_main_keyboard())
            continue   # важно: прерываем дальнейшую обработку

                # ==============================================
        # БЛОК 6: ПРОВЕРКА СОСТОЯНИЙ ПОЛЬЗОВАТЕЛЯ (ожидание ввода)
        # ==============================================
        
        # Состояния для спонсоров (оплата)
        if user_id in waiting_for_payment_photo:
            is_admin = user_id in ADMIN_IDS
            handle_payment_photo(vk, user_id, event.attachments, send_message, ADMIN_IDS, is_admin)
            continue

        if user_id in waiting_for_reset_confirm:
            is_admin = user_id in ADMIN_IDS
            handle_reset_confirm(vk, user_id, text, send_message, is_admin)
            continue

        if user_id in waiting_for_payment_amount:
            is_admin = user_id in ADMIN_IDS
            handle_payment_amount(vk, user_id, text, send_message, is_admin, ADMIN_IDS)
            continue    

        # Состояния для турниров (объявление тура)
        if user_id in waiting_for_tour_announcement:
            handle_tour_announcement_input(vk, user_id, text, send_message)
            continue

        # Состояния для регистрации спонсора
        if is_waiting_for_name(user_id):
            is_admin = user_id in ADMIN_IDS
            handle_name_input(vk, user_id, text, send_message, is_admin)
            continue

        if is_waiting_for_unsubscribe(user_id):
            is_admin = user_id in ADMIN_IDS
            handle_unsubscribe_confirm(vk, user_id, text, send_message, is_admin)
            continue

        # Состояния для пользовательских турниров (выбор турнира, регистрация)
        if user_id in waiting_for_tournament_choice:
            is_admin = user_id in ADMIN_IDS
            handle_tournament_selection(vk, user_id, text, send_message, is_admin)
            continue
        
        if user_id in waiting_for_registration_name:
            handle_registration_name(vk, user_id, text, send_message)
            continue
        
        if user_id in waiting_for_registration_army:
            handle_registration_army(vk, user_id, text, send_message, ADMIN_IDS)
            continue
        
        if user_id in waiting_for_match_result:
            handle_match_result(vk, user_id, text, send_message)
            continue

        # Админские состояния для турниров (создание)
        if user_id in waiting_for_new_tournament_name:
            handle_new_tournament_name(vk, user_id, text, send_message)
            continue
        
        if user_id in waiting_for_new_tournament_date:
            handle_new_tournament_date(vk, user_id, text, send_message)
            continue
        
        if user_id in waiting_for_new_tournament_max_players:
            handle_new_tournament_max_players(vk, user_id, text, send_message)
            continue
        # ============================================================
        # БЛОК 7: ОБРАБОТКА КОМАНД (КНОПОК И ТЕКСТА)
        # ============================================================

        # --- ГЛАВНОЕ МЕНЮ (кнопки /start, ТУРНИРЫ, СПОНСОР, КЛЮЧИ) ---
        if text == "/start":
            # Сбрасываем выбранный турнир для этого пользователя
            if user_id in selected_tournament:
                del selected_tournament[user_id]
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

        elif text == "🏆 ТУРНИРЫ":
            # Заглушка на время разработки 
            send_message(vk, user_id, "🚧 Пока В разработке")   

            # Сбрасываем выбранный турнир (начинаем с чистого листа)
            #if user_id in selected_tournament:
            #    del selected_tournament[user_id]
            # Очищаем состояния ожидания
            #if user_id in waiting_for_tournament_choice:
            #    del waiting_for_tournament_choice[user_id]
            #is_admin = user_id in ADMIN_IDS
            #send_message(vk, user_id, "🏆 Раздел ТУРНИРЫ\n\nВыберите действие:",
            #           get_tournament_keyboard(is_admin=is_admin))

        elif text == "💰 СПОНСОР":
            is_admin = user_id in ADMIN_IDS
            is_sponsor_flag = is_sponsor(user_id)
            send_message(vk, user_id, "💰 Меню спонсора\n\nВыберите действие:",
            get_sponsor_keyboard(is_sponsor=is_sponsor_flag, is_admin=is_admin))
        
        elif text == "🔑 КЛЮЧИ":
            send_message(vk, user_id, "🔑 Раздел КЛЮЧИ\n\nВыберите действие:",
                        get_key_keyboard())

        # ============================================================
        # ТУРНИРЫ – ВЕТКА 1: ГЛАВНОЕ МЕНЮ ТУРНИРОВ (get_tournament_keyboard)
        # ============================================================
        elif text == "📋 Список турниров":
            # Показывает список активных турниров (для всех пользователей)
            is_admin = user_id in ADMIN_IDS
            handle_list_tournaments_user(vk, user_id, send_message, is_admin)

        elif text == "➕ Управление турнирами" and user_id in ADMIN_IDS:
            send_message(vk, user_id, "⚙️ Управление турнирами:",
            get_tournament_user_keyboard(is_admin=True))

        # ============================================================
        # ТУРНИРЫ – ВЕТКА 2: УПРАВЛЕНИЕ ТУРНИРАМИ (get_tournament_user_keyboard)
        # ============================================================
        elif text == "📋 Выбрать турнир":
            # Выбор турнира для регистрации/оплаты/начала (для всех)
            is_admin = user_id in ADMIN_IDS
            handle_list_tournaments_user(vk, user_id, send_message, is_admin)
            
        elif text == "➕ Создать турнир" and user_id in ADMIN_IDS:
            # Создание нового турнира (админ)
            handle_admin_create_tournament(vk, user_id, send_message)

        elif text == "🗑️ Удалить турнир" and user_id in ADMIN_IDS:
            # Удаление турнира (админ)
            handle_admin_delete_tournament(vk, user_id, send_message)

        elif text == "📢 Сообщение о туре" and user_id in ADMIN_IDS:
            handle_tour_announcement(vk, user_id, send_message)

        elif text == "🏁 Завершить турнир" and user_id in ADMIN_IDS:
            handle_finish_tournament(vk, user_id, send_message)

        # ============================================================
        # ТУРНИРЫ – ВЕТКА 3: ДЕЙСТВИЯ С ВЫБРАННЫМ ТУРНИРОМ (get_tournament_actions_keyboard)
        # ============================================================
        elif text == "📝 Зарегистрироваться":
            # Регистрация на выбранный турнир (для незарегистрированных)
            handle_register_user(vk, user_id, send_message)

        elif text == "✏️ Редактировать мои данные":
            handle_edit_my_data(vk, user_id, send_message)

        elif text == "💳 Внести оплату":
            # Отправка фото оплаты админу
            handle_payment(vk, user_id, send_message)

        elif text == "▶️ Начать турнир" and user_id in ADMIN_IDS:
            # Вызываем функцию рассылки сообщения о начале турнира
            handle_tournament_start(vk, user_id, send_message)

        elif text == "👥 Список игроков":
            # Показать список игроков (для всех)
            handle_show_players_list(vk, user_id, send_message)

        elif text == "⚙️ Управление игроками" and user_id in ADMIN_IDS:
            # Переход в меню управления игроками (админ)
            if user_id not in selected_tournament:
                send_message(vk, user_id, "❌ Сначала выберите турнир через 'Выбрать турнир'.")
            else:
                tournament = selected_tournament[user_id]
                send_message(vk, user_id, f"👥 Управление игроками турнира '{tournament['name']}':",
                get_players_menu_keyboard(is_admin=True))

        # ============================================================
        # ТУРНИРЫ – ВЕТКА 4: УПРАВЛЕНИЕ ИГРОКАМИ (get_players_menu_keyboard)
        # ============================================================
        elif text == "📋 Показать список игроков":
            # (дублирует кнопку выше, но оставим для обеих веток)
            handle_show_players_list(vk, user_id, send_message)

        elif text == "🗑️ Удалить игрока" and user_id in ADMIN_IDS:
            # TODO: удаление игрока из турнира
            send_message(vk, user_id, "🚧 Удаление игрока в разработке.")

        elif text == "🔗 Создать пары" and user_id in ADMIN_IDS:
            # TODO: создание пар для текущего раунда
            send_message(vk, user_id, "🚧 Создание пар в разработке.")

        elif text == "⚙️ Действия с турниром" and user_id in ADMIN_IDS:
            # Переход в подменю действий с турниром
            if user_id not in selected_tournament:
                send_message(vk, user_id, "❌ Сначала выберите турнир.")
            else:
                send_message(vk, user_id, "⚙️ Действия с турниром:",
                             get_event_actions_menu_keyboard())

        # ============================================================
        # ТУРНИРЫ – ВЕТКА 5: ДЕЙСТВИЯ С ТУРНИРОМ (get_event_actions_menu_keyboard)
        # ============================================================
        elif text == "📨 Показать игрокам пары" and user_id in ADMIN_IDS:
            # TODO: рассылка пар игрокам
            send_message(vk, user_id, "🚧 Рассылка пар в разработке.")

        elif text == "🏆 Показать таблицу лидеров":
            # Показать таблицу лидеров (доступно всем)
            if user_id not in selected_tournament:
                send_message(vk, user_id, "❌ Сначала выберите турнир.")
            else:
                tournament = selected_tournament[user_id]
                leaderboard = db.get_leaderboard(tournament['id'])
                if leaderboard:
                    text_leader = "🏆 ТАБЛИЦА ЛИДЕРОВ:\n\n"
                    for idx, (reg_id, uid, name, to, vp) in enumerate(leaderboard, 1):
                        text_leader += f"{idx}. {name} — ТО: {to}, ВП: {vp}\n"
                    send_message(vk, user_id, text_leader)
                else:
                    send_message(vk, user_id, "📋 Нет данных для отображения.")

        elif text == "✏️ Редактировать таблицу лидеров" and user_id in ADMIN_IDS:
            # TODO: редактирование очков игроков
            send_message(vk, user_id, "🚧 Редактирование таблицы лидеров в разработке.")

        # ============================================================
        # КНОПКИ СПОНСОРОВ
        # ============================================================

        elif text == "💰 Стать спонсором":
            is_admin = user_id in ADMIN_IDS
            handle_become_sponsor(vk, user_id, send_message, is_admin)

        elif text == "✅ Подтвердить оплату":
            handle_payment_request(vk, user_id, send_message)

        elif text == "❌ Отписаться":
            # Запускаем процесс отписки (устанавливаем состояние ожидания)
            handle_unsubscribe_confirm(vk, user_id, send_message)

        elif text == "🔄 Сбросить месячные суммы" and user_id in ADMIN_IDS:
            handle_reset_monthly(vk, user_id, send_message, is_admin=True)

        elif text == "📋 Показать список спонсоров" and user_id in ADMIN_IDS:
            handle_show_sponsors(vk, user_id, send_message, is_admin=True)

        elif text == "📢 Напомнить об оплате" and user_id in ADMIN_IDS:
            handle_remind_payment(vk, user_id, send_message, is_admin=True)

        # ============================================================
        # КНОПКИ КЛЮЧЕЙ
        # ============================================================
        elif text == "🔑 Взять ключ":
            handle_take_key(vk, user_id, send_message, ADMIN_IDS)

        elif text == "🔓 Отдать ключ":
            handle_return_key(vk, user_id, send_message, ADMIN_IDS)

        elif text == "❓ Кто держит ключ":
            handle_who_has_key(vk, user_id, send_message)

    
        # ============================================================
        # НЕИЗВЕСТНАЯ КОМАНДА
        # ============================================================
        else:
            send_message(vk, user_id, "🏠 Главное меню:", get_main_keyboard())