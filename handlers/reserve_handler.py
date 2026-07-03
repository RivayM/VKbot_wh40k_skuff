# handlers/reserve_handler.py
import logging
import datetime
import re
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from database import reserve_db as rdb
from keyboards_reserve import get_reserve_date_keyboard, get_reserve_table_keyboard, get_reserve_table_actions_keyboard
from utils.helpers import send_message

logger = logging.getLogger(__name__)

# Хранилища состояний
waiting_for_date = {}            # user_id -> True (ожидание выбора даты)
waiting_for_table = {}           # user_id -> {'date': date_str} (ожидание выбора стола)
waiting_for_action = {}          # user_id -> {'date': date_str, 'table': table_num, 'slot': slot} (выбор действия)

def get_user_name(vk, user_id):
    try:
        user = vk.users.get(user_ids=user_id)[0]
        return f"{user['first_name']} {user['last_name']}"
    except:
        return f"id{user_id}"

def handle_reserve_menu(vk, user_id, send_message_func):
    """Показывает календарь с датами"""
    rdb.clean_old_reserves()
    waiting_for_date[user_id] = True
    if user_id in waiting_for_table:
        del waiting_for_table[user_id]
    if user_id in waiting_for_action:
        del waiting_for_action[user_id]
    send_message_func(vk, user_id, "📅 Выберите дату для бронирования стола:", get_reserve_date_keyboard())

def handle_date_selection(vk, user_id, text, send_message_func):
    """Обработка выбора даты -> показывает выбор столов и времени"""
    if user_id not in waiting_for_date:
        return False
    
    match = re.search(r'\d{2}\.\d{2}', text)
    if not match:
        send_message_func(vk, user_id, "❌ Пожалуйста, выберите дату из календаря.")
        return True
    
    date_str = match.group(0)
    try:
        day, month = map(int, date_str.split('.'))
        today = datetime.date.today()
        year = today.year if month >= today.month else today.year + 1
        selected_date = datetime.date(year, month, day)
        if selected_date < today:
            send_message_func(vk, user_id, "❌ Нельзя выбрать прошедшую дату.")
            return True
        iso_date = selected_date.isoformat()
        
        # 👇 ПЕРЕНЕСИТЕ PRINT СЮДА (после создания iso_date)
        print(f"[DEBUG] Выбрана дата: iso_date={iso_date}")
        
    except Exception as e:
        print(f"[DEBUG] Ошибка парсинга даты: {e}")
        send_message_func(vk, user_id, "❌ Пожалуйста, выберите дату из календаря.")
        return True
    
    waiting_for_table[user_id] = {'date': iso_date}
    del waiting_for_date[user_id]
    
    send_message_func(vk, user_id, f"📅 Вы выбрали {date_str}\n\nВыберите стол и время:", 
                      get_reserve_table_keyboard(date_str=iso_date))
    return True

def handle_table_selection(vk, user_id, text, send_message_func, admin_ids):
    """Обработка выбора стола -> показывает действия"""
    if user_id not in waiting_for_table:
        return False
    
    match = re.search(r'(☀️|🌙)?\s*Стол\s*(\d+)', text, re.IGNORECASE)
    if not match:
        send_message_func(vk, user_id, "❌ Пожалуйста, выберите стол из меню.")
        return True
    
    slot_emoji = match.group(1) or ''
    table_num = int(match.group(2))
    if table_num not in range(1, 5):
        send_message_func(vk, user_id, "❌ Пожалуйста, выберите стол из меню (1-4).")
        return True
    
    if '☀️' in slot_emoji:
        time_slot = 1
        slot_name = "утро"
    elif '🌙' in slot_emoji:
        time_slot = 2
        slot_name = "вечер"
    else:
        time_slot = 1
        slot_name = "утро"
    
    data = waiting_for_table[user_id]
    date_str = data['date']
    
    is_free = rdb.is_slot_free(table_num, date_str, time_slot)
    if is_free:
        waiting_for_action[user_id] = {
            'date': date_str,
            'table': table_num,
            'slot': time_slot,
            'slot_name': slot_name,
            'is_occupied': False
        }
        del waiting_for_table[user_id]
        send_message_func(vk, user_id, f"🪑 Стол {table_num}, {slot_name} свободен.\n\nВыберите действие:", 
                          get_reserve_table_actions_keyboard(is_reserved=False, is_owner=False))
    else:
        info = rdb.get_reserve_info(table_num, date_str, time_slot)
        if info:
            user_name = info['name']
            user_link = f"https://vk.com/id{info['user_id']}"
            is_owner = (info['user_id'] == user_id)
            waiting_for_action[user_id] = {
                'date': date_str,
                'table': table_num,
                'slot': time_slot,
                'slot_name': slot_name,
                'is_occupied': True
            }
            del waiting_for_table[user_id]
            msg = f"🪑 Стол {table_num}, {slot_name} уже зарезервирован.\n👤 {user_name} ({user_link})"
            send_message_func(vk, user_id, msg, 
                              get_reserve_table_actions_keyboard(is_reserved=True, is_owner=is_owner))
        else:
            send_message_func(vk, user_id, "❌ Ошибка: слот не найден.")
    return True

def handle_take_reserve(vk, user_id, send_message_func, admin_ids):
    """Создаёт резерв по кнопке 'Зарезервировать'"""
    if user_id not in waiting_for_action:
        send_message_func(vk, user_id, "❌ Сначала выберите дату и стол.")
        return
    data = waiting_for_action.pop(user_id)
    if data.get('is_occupied'):
        send_message_func(vk, user_id, "❌ Этот слот уже занят, резерв невозможен.")
        handle_reserve_menu(vk, user_id, send_message_func)
        return
    
    table_num = data['table']
    date_str = data['date']
    time_slot = data['slot']
    slot_name = data['slot_name']
    user_name = get_user_name(vk, user_id)
    
    rdb.create_reserve(table_num, date_str, time_slot, user_id, user_name)
    date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    date_display = date_obj.strftime('%d.%m')
    
    send_message_func(vk, user_id, f"✅ Стол {table_num} зарезервирован на {date_display} ({slot_name})!")
    for admin_id in admin_ids:
        try:
            send_message_func(vk, admin_id,
                f"🎲 **Новый резерв стола**\n"
                f"🪑 Стол {table_num}\n"
                f"📅 {date_display} ({slot_name})\n"
                f"👤 {user_name} (https://vk.com/id{user_id})")
        except:
            pass
    handle_reserve_menu(vk, user_id, send_message_func)

def handle_cancel_reserve_from_action(vk, user_id, send_message_func):
    """Снимает резерв (если пользователь владелец)"""
    if user_id not in waiting_for_action:
        send_message_func(vk, user_id, "❌ Сначала выберите дату и стол.")
        return
    data = waiting_for_action.get(user_id)
    if not data:
        return
    
    table_num = data['table']
    date_str = data['date']
    time_slot = data['slot']
    slot_name = data['slot_name']
    
    info = rdb.get_reserve_info(table_num, date_str, time_slot)
    if not info or info['user_id'] != user_id:
        send_message_func(vk, user_id, "❌ Вы не можете снять этот резерв (не владелец).")
        handle_reserve_menu(vk, user_id, send_message_func)
        return
    
    rdb.cancel_reserve(table_num, date_str, time_slot)
    date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    date_display = date_obj.strftime('%d.%m')
    send_message_func(vk, user_id, f"✅ Резерв на {date_display} ({slot_name}) отменён.")
    waiting_for_action.pop(user_id, None)
    handle_reserve_menu(vk, user_id, send_message_func)

def handle_view_reserve_from_action(vk, user_id, send_message_func):
    """Показывает информацию о резерве"""
    if user_id not in waiting_for_action:
        send_message_func(vk, user_id, "❌ Сначала выберите дату и стол.")
        return
    data = waiting_for_action.get(user_id)
    if not data:
        return
    
    table_num = data['table']
    date_str = data['date']
    time_slot = data['slot']
    slot_name = data['slot_name']
    
    info = rdb.get_reserve_info(table_num, date_str, time_slot)
    if info:
        user_link = f"https://vk.com/id{info['user_id']}"
        date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        date_display = date_obj.strftime('%d.%m')
        send_message_func(vk, user_id, f"🪑 Стол {table_num}, {date_display} ({slot_name})\n👤 {info['name']} ({user_link})")
    else:
        send_message_func(vk, user_id, "❌ Резерв не найден (возможно, был отменён).")
    handle_reserve_menu(vk, user_id, send_message_func)

def handle_back(vk, user_id, send_message_func):
    """Обработка кнопки 'Назад' из любого меню резерва"""
    states = [waiting_for_date, waiting_for_table, waiting_for_action]
    for state in states:
        if user_id in state:
            del state[user_id]
    handle_reserve_menu(vk, user_id, send_message_func)

def clear_reserve_states(user_id):
    """Очищает все состояния резерва для пользователя"""
    states = [waiting_for_date, waiting_for_table, waiting_for_action]
    for state in states:
        if user_id in state:
            del state[user_id]

# Функции для проверки состояний (для bot.py)
def is_waiting_for_date(user_id):
    return user_id in waiting_for_date

def is_waiting_for_table(user_id):
    return user_id in waiting_for_table

def is_waiting_for_action(user_id):
    return user_id in waiting_for_action