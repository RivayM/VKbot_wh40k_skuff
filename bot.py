# ==================================================
# БЛОК 1: ИМПОРТ БИБЛИОТЕК И НАСТРОЙКИ
# ==================================================
import vk_api
import os
import logging
from dotenv import load_dotenv
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType

# Модули обработчиков
from handlers.tournament_user import *          # всё из турниров
from handlers.key_handler import handle_take_key, handle_return_key, handle_who_has_key
from handlers.sponsorship import *  
from handlers.event_handlers import *

# Клавиатуры
from keyboards import *  
from keyboards_event import *
from handlers.reserve_handler import (
    waiting_for_reserve_table,
    waiting_for_slot_action,
    selected_table,
    handle_reserve_menu,
    handle_table_selection,
    handle_slot_selection,
    handle_take_reserve,
    handle_cancel_reserve_from_action,
    handle_view_reserve_from_action,
    is_waiting_for_reserve_table
)
# Утилиты
from utils.helpers import send_message, extract_photo_url

# Инициализация таблиц
from database.tournament_db import init_tournament_tables
from database.events_db import init_events_table

# Общие функции базы данных
from database.reserve_db import init_reserve_table
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
init_events_table()    # таблица ивентов
init_reserve_table()   # таблица резерве

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

             # ИВЕНТЫ (кнопка назад)
            if user_id in waiting_for_event_name:
                del waiting_for_event_name[user_id]
            if user_id in waiting_for_event_date:
                del waiting_for_event_date[user_id]
            if user_id in waiting_for_event_choice:
                del waiting_for_event_choice[user_id]
            if user_id in waiting_for_remove_participant:
                del waiting_for_remove_participant[user_id]
            if user_id in waiting_for_event_payment:
                del waiting_for_event_payment[user_id]

            # Очистка состояний резерва столов
            if user_id in waiting_for_reserve_table:
                del waiting_for_reserve_table[user_id]
            if user_id in waiting_for_slot_action:
                del waiting_for_slot_action[user_id]
            if user_id in selected_table:
                del selected_table[user_id]

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
            # удалить спонсора
            if user_id in waiting_for_remove_sponsor:
                del waiting_for_remove_sponsor[user_id]

            if user_id in waiting_for_event_name:
                del waiting_for_event_name[user_id]
            if user_id in waiting_for_event_choice:
                del waiting_for_event_choice[user_id]

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
        
        # 1. Сначала проверяем удаление участника (это состояние должно быть самым приоритетным)
        if user_id in waiting_for_remove_participant:
            print("[DEBUG] Обнаружено waiting_for_remove_participant, вызываем подтверждение")
            handle_remove_participant_confirm(vk, user_id, text, send_message)
            continue

        # 2. Затем оплата мероприятий
        if user_id in waiting_for_event_payment:
            print("[DEBUG] УСЛОВИЕ СРАБОТАЛО! Вызываем handle_event_payment_amount")
            is_admin = user_id in ADMIN_IDS
            handle_event_payment_amount(vk, user_id, text, send_message, is_admin)
            continue

        # 3. Затем состояния мероприятий (выбор, удаление мероприятия, действия)
        if is_waiting_for_event_name(user_id):
            is_admin = user_id in ADMIN_IDS
            handle_event_name_input(vk, user_id, text, send_message, is_admin)
            continue

        if is_waiting_for_event_date(user_id):
            is_admin = user_id in ADMIN_IDS
            handle_event_date_input(vk, user_id, text, send_message, is_admin)
            continue

        if is_waiting_for_event_choice(user_id):
            state = waiting_for_event_choice.get(user_id)
            if state:
                step = state['step']
                if step == 'list':
                    if handle_event_choice(vk, user_id, text, send_message, is_admin=user_id in ADMIN_IDS):
                        continue
                elif step == 'delete':
                    if handle_delete_choice(vk, user_id, text, send_message, is_admin=user_id in ADMIN_IDS):
                        continue
                elif step == 'selected':
                    if text in ("📋 Посмотреть участников", "⚠️ Удалить участника (админ)"):
                        if text == "📋 Посмотреть участников":
                            is_admin = user_id in ADMIN_IDS
                            handle_show_participants(vk, user_id, send_message, state['event_id'], state['event_name'], is_admin)
                        elif text == "⚠️ Удалить участника (админ)" and user_id in ADMIN_IDS:
                            handle_remove_participant_start(vk, user_id, send_message, state['event_id'])
                        continue
                    else:
                        if handle_event_action(vk, user_id, text, send_message, is_admin=user_id in ADMIN_IDS):
                            continue
            continue
        

        # ==============================================   
        # Состояния для спонсоров (оплата)
        # ============================================== 
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

        if user_id in waiting_for_remove_sponsor:
            is_admin = user_id in ADMIN_IDS
            handle_remove_sponsor_confirm(vk, user_id, text, send_message, is_admin)
            continue
        # ============================================================
        # Резерв столов
        # ============================================================
        if is_waiting_for_reserve_table(user_id):
            handle_slot_selection(vk, user_id, text, send_message, ADMIN_IDS)
            continue

        # ============================================================
        # БЛОК 7: ОБРАБОТКА КОМАНД (КНОПОК И ТЕКСТА)
        # ============================================================
        print(f"[DEBUG] Блок7: текст='{text}', user={get_user_name(vk, user_id)}")
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
            continue

        elif text == "🏆 ТУРНИРЫ":
            send_message(vk, user_id, "🚧 Пока В разработке")   
            continue

        elif text == "📋 МЕРОПРИЯТИЯ":
            is_admin = user_id in ADMIN_IDS
            handle_events_menu(vk, user_id, send_message, is_admin=is_admin)
            continue
        elif text == "💰 СПОНСОР":
            is_admin = user_id in ADMIN_IDS
            is_sponsor_flag = is_sponsor(user_id)
            send_message(vk, user_id, "💰 Меню спонсора\n\nВыберите действие:",
            get_sponsor_keyboard(is_sponsor=is_sponsor_flag, is_admin=is_admin))
            continue
        elif text == "🔑 КЛЮЧИ":
            send_message(vk, user_id, "🔑 Раздел КЛЮЧИ\n\nВыберите действие:",
                        get_key_keyboard())
            continue
        # ============================================================
        # ---------- МЕРОПРИЯТИЯ ----------
        # ============================================================

        elif text == "➕ Создать мероприятие" and user_id in ADMIN_IDS:
            handle_create_event(vk, user_id, send_message)
            continue

        elif text == "🗑️ Удалить мероприятие" and user_id in ADMIN_IDS:
            handle_delete_event(vk, user_id, send_message, is_admin=True)
            continue

        elif text == "📋 Список мероприятий":
            handle_list_events(vk, user_id, send_message)
            continue     

        # ============================================================
        # Обработка выбора стола
        # ============================================================
        elif text == "🎲 Резерв стола":
            handle_reserve_menu(vk, user_id, send_message)
            continue

        elif text.startswith("🎲 Стол "):
            handle_table_selection(vk, user_id, text, send_message)
            continue

        elif text == "📝 Зарезервировать":
            handle_take_reserve(vk, user_id, send_message, ADMIN_IDS)
            continue

        elif text == "❌ Снять резерв":
            handle_cancel_reserve_from_action(vk, user_id, send_message)
            continue

        elif text == "👥 Просмотреть резерв":
            handle_view_reserve_from_action(vk, user_id, send_message)
            continue
        # ============================================================
        # КНОПКИ СПОНСОРОВ
        # ============================================================

        elif text == "💰 Стать спонсором":
            is_admin = user_id in ADMIN_IDS
            handle_become_sponsor(vk, user_id, send_message, is_admin)
            continue     
        elif text == "✅ Подтвердить оплату":
            handle_payment_request(vk, user_id, send_message)
            continue
        elif text == "❌ Отписаться":
            # Запускаем процесс отписки (устанавливаем состояние ожидания)
            handle_unsubscribe(vk, user_id, send_message)
            continue
        elif text == "🔄 Сбросить месячные суммы" and user_id in ADMIN_IDS:
            handle_reset_monthly(vk, user_id, send_message, is_admin=True)
            continue
        elif text == "📋 Показать список спонсоров" and user_id in ADMIN_IDS:
            handle_show_sponsors(vk, user_id, send_message, is_admin=True)
            continue
        elif text == "📢 Напомнить об оплате" and user_id in ADMIN_IDS:
            handle_remind_payment(vk, user_id, send_message, is_admin=True)
            continue

        elif text == "🗑️ Удалить спонсора" and user_id in ADMIN_IDS:
            handle_remove_sponsor_start(vk, user_id, send_message)
            continue
        # ============================================================
        # КНОПКИ КЛЮЧЕЙ
        # ============================================================
        elif text == "🔑 Взять ключ":
            handle_take_key(vk, user_id, send_message, ADMIN_IDS)
            continue
        elif text == "🔓 Отдать ключ":
            handle_return_key(vk, user_id, send_message, ADMIN_IDS)
            continue
        elif text == "❓ Кто держит ключ":
            handle_who_has_key(vk, user_id, send_message)
            continue
    
        # ============================================================
        # НЕИЗВЕСТНАЯ КОМАНДА
        # ============================================================
        else:
            send_message(vk, user_id, "🏠 Главное меню:", get_main_keyboard())  
            continue