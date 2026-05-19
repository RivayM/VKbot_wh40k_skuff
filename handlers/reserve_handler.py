# handlers/reserve_handler.py
import logging
from keyboards_reserve import (
    get_reserve_main_keyboard,
    get_reserve_table_actions_keyboard
)

logger = logging.getLogger(__name__)

# Хранилище резервов (потом можно перенести в БД)
reserves = {
    1: None,   # None - свободен, иначе {'user_id': xxx, 'name': '...', 'time': '...', 'with': '...'}
    2: None,
    3: None,
    4: None
}
waiting_for_reserve_details = {}  # user_id -> {'table': int}
waiting_for_cancel_confirm = {}   # user_id -> {'table': int}
selected_table = {}               # user_id -> table_num (для действий)

def get_tables_status():
    """Возвращает словарь {номер_стола: зарезервирован ли}"""
    return {num: reserves[num] is not None for num in reserves}

def get_reserve_info(table):
    return reserves.get(table)

def reserve_table(table, user_id, user_name, time_text, user_link, with_text=""):
    reserves[table] = {
        'user_id': user_id,
        'name': user_name,
        'link': user_link,
        'time': time_text,
        'with': with_text
    }
    return True

def cancel_reserve(table):
    reserves[table] = None
    return True

def is_owner(table, user_id):
    info = reserves.get(table)
    return info is not None and info['user_id'] == user_id

# ---------- Вспомогательная функция для получения имени ----------
def get_user_info(vk, user_id):
    """Возвращает (имя, ссылка)"""
    try:
        user = vk.users.get(user_ids=user_id)[0]
        name = f"{user['first_name']} {user['last_name']}"
        link = f"https://vk.com/id{user_id}"
        return name, link
    except:
        return f"id{user_id}", f"https://vk.com/id{user_id}"

# ---------- Обработчики ----------
def handle_reserve_menu(vk, user_id, send_message_func):
    tables_status = get_tables_status()
    send_message_func(vk, user_id, "🎲 Выберите стол:", get_reserve_main_keyboard(tables_status))

def handle_table_selection(vk, user_id, text, send_message_func):
    # Извлекаем номер стола из текста кнопки (например, "🎲 Стол 1")
    if not text.startswith('🎲 Стол '):
        return False
    try:
        table_num = int(text.split()[-1])
    except:
        return False
    if table_num not in range(1, 5):
        return False
    
    selected_table[user_id] = table_num
    info = reserves.get(table_num)
    if info is None:
        # Стол свободен – предложить зарезервировать
        waiting_for_reserve_details[user_id] = {'table': table_num}
        send_message_func(vk, user_id, f"🎲 Стол {table_num} свободен.\n\n"
                                       "✏️ Введите время и с кем будете играть (например: '19:00, с Иваном'):")
    else:
        # Стол занят
        info = reserves[table_num]
        is_owner_flag = (info['user_id'] == user_id)
        # Добавляем ссылку на профиль
        user_link = f"https://vk.com/id{info['user_id']}"
        msg = f"🎲 Стол {table_num} зарезервирован.\n"
        msg += f"👤 Кем: {info['name']} ({user_link})\n"
        msg += f"⏰ Время: {info['time']}\n"
        if info.get('with'):
            msg += f"🎲 С кем: {info['with']}\n"
        msg += "\n"
        send_message_func(vk, user_id, msg, get_reserve_table_actions_keyboard(is_reserved=True, is_owner=is_owner_flag))
    return True

def handle_reserve_details(vk, user_id, text, send_message_func, admin_ids=None, is_admin=False):
    if user_id not in waiting_for_reserve_details:
        return False
    data = waiting_for_reserve_details.pop(user_id)
    table_num = data['table']
    user_name, user_link = get_user_info(vk, user_id)
    time_and_with = text.strip()
    # Сохраняем всю строку в 'time', а 'with' оставляем пустым (или можно разделить)
    reserve_table(table_num, user_id, user_name, time_and_with, user_link, with_text="")
    for admin_id in admin_ids or []:
        send_message_func(vk, admin_id, 
            f"🎲 **Резерв стола {table_num}**\n"
            f"👤 {user_name} ({user_link})\n"
            f"📝 {time_and_with}")
    send_message_func(vk, user_id, f"✅ Стол {table_num} зарезервирован!", 
                      get_reserve_main_keyboard(get_tables_status()))
    return True



def handle_cancel_reserve(vk, user_id, send_message_func, table_num, admin_ids=None):
    info = reserves.get(table_num)
    if not info:
        send_message_func(vk, user_id, f"❌ Стол {table_num} не зарезервирован.")
        return
    # Проверяем, может ли пользователь снять резерв
    if info['user_id'] != user_id and (not admin_ids or user_id not in admin_ids):
        send_message_func(vk, user_id, "❌ Вы не можете снять этот резерв.")
        return
    waiting_for_cancel_confirm[user_id] = {'table': table_num}
    send_message_func(vk, user_id, f"⚠️ Вы уверены, что хотите снять резерв со стола {table_num}? (да/нет)")

def handle_cancel_confirm(vk, user_id, text, send_message_func):
    if user_id not in waiting_for_cancel_confirm:
        return False
    data = waiting_for_cancel_confirm.pop(user_id)
    if text.lower() in ['да', 'yes', 'y']:
        cancel_reserve(data['table'])
        send_message_func(vk, user_id, f"✅ Резерв стола {data['table']} снят.", 
                          get_reserve_main_keyboard(get_tables_status()))
    else:
        send_message_func(vk, user_id, "❌ Отмена снятия резерва.", 
                          get_reserve_main_keyboard(get_tables_status()))
    return True

def handle_show_reserve(vk, user_id, send_message_func, table_num):
    info = reserves.get(table_num)
    if not info:
        send_message_func(vk, user_id, f"❌ Стол {table_num} не зарезервирован.")
        return
    msg = f"🎲 Стол {table_num}\n"
    msg += f"👤 Зарезервировал: {info['name']} ({info['link']})\n"
    msg += f"⏰ Время: {info['time']}\n"
    if info.get('with'):
        msg += f"🎲 С кем: {info['with']}"
    send_message_func(vk, user_id, msg)

# ---------- Функции для проверки состояний ----------
def is_waiting_for_reserve_details(user_id):
    return user_id in waiting_for_reserve_details

def is_waiting_for_cancel_confirm(user_id):
    return user_id in waiting_for_cancel_confirm