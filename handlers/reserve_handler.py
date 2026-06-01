# handlers/reserve_handler.py
import logging
import datetime
import re
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from database import reserve_db as rdb
from keyboards_reserve import get_reserve_main_keyboard, get_reserve_table_actions_keyboard
from utils.helpers import send_message

logger = logging.getLogger(__name__)

# Хранилища состояний
waiting_for_reserve_table = {}
selected_table = {}
waiting_for_slot_action = {}

def get_user_name(vk, user_id):
    try:
        user = vk.users.get(user_ids=user_id)[0]
        return f"{user['first_name']} {user['last_name']}"
    except:
        return f"id{user_id}"

def handle_reserve_menu(vk, user_id, send_message_func):
    """Главное меню выбора стола"""
    rdb.clean_old_reserves()
    tables_status = {1: False, 2: False, 3: False, 4: False}
    send_message_func(vk, user_id, "🎲 Выберите стол:", get_reserve_main_keyboard(tables_status))

def handle_table_selection(vk, user_id, text, send_message_func):
    """Выбор стола -> показывает клавиатуру с датами и временными слотами"""
    if not text.startswith('🎲 Стол '):
        return False
    try:
        table_num = int(text.split()[-1])
    except:
        return False
    if table_num not in range(1,5):
        return False

    selected_table[user_id] = table_num
    waiting_for_reserve_table[user_id] = {'table': table_num}

    keyboard = VkKeyboard(one_time=False)
    today = datetime.date.today()
    for i in range(4):
        date_obj = today + datetime.timedelta(days=i)
        date_str = date_obj.strftime('%d.%m.%Y')
        iso_date = date_obj.isoformat()
        for slot in [1,2]:
            slot_name = "утро" if slot == 1 else "вечер"
            is_free = rdb.is_slot_free(table_num, iso_date, slot)
            if is_free:
                emoji = "☀️" if slot == 1 else "🌙"
                btn_text = f'{emoji} {date_str} ({slot_name})'
                color = VkKeyboardColor.POSITIVE
            else:
                btn_text = f'❌ {date_str} ({slot_name}) – занято'
                color = VkKeyboardColor.NEGATIVE
            keyboard.add_button(btn_text, color=color)
            keyboard.add_line()
    keyboard.add_button('🔙 Назад', color=VkKeyboardColor.NEGATIVE)
    send_message_func(vk, user_id, "🎲 Выберите дату и время:", keyboard)
    return True

def handle_slot_selection(vk, user_id, text, send_message_func, admin_ids):
    """Обработка выбора слота – показывает информацию и клавиатуру действий (без уведомлений)"""
    if user_id not in waiting_for_reserve_table:
        return False
    data = waiting_for_reserve_table.pop(user_id)
    table_num = data['table']

    if text == "🔙 Назад":
        handle_reserve_menu(vk, user_id, send_message_func)
        return True

    # Извлекаем дату с помощью регулярного выражения
    match = re.search(r'\d{2}\.\d{2}\.\d{4}', text)
    if not match:
        send_message_func(vk, user_id, "❌ Не удалось распознать дату.")
        waiting_for_reserve_table[user_id] = {'table': table_num}
        handle_table_selection(vk, user_id, f'🎲 Стол {table_num}', send_message_func)
        return True
    date_str = match.group(0)
    try:
        iso_date = datetime.datetime.strptime(date_str, '%d.%m.%Y').date().isoformat()
    except:
        send_message_func(vk, user_id, "❌ Неверная дата.")
        return True

    # Определяем слот
    if 'утро' in text:
        time_slot = 1
        slot_name = "утро"
    elif 'вечер' in text:
        time_slot = 2
        slot_name = "вечер"
    else:
        send_message_func(vk, user_id, "❌ Не удалось определить время.")
        return True

    # Проверяем свободен ли слот
    is_free = rdb.is_slot_free(table_num, iso_date, time_slot)

    if is_free:
        waiting_for_slot_action[user_id] = {
            'table': table_num,
            'date': iso_date,
            'slot': time_slot,
            'date_str': date_str,
            'slot_name': slot_name
        }
        send_message_func(vk, user_id, f"🎲 Стол {table_num}, {date_str} ({slot_name}) свободен.\n\nВыберите действие:",
                          get_reserve_table_actions_keyboard(is_reserved=False, is_owner=False))
    else:
        info = rdb.get_reserve_info(table_num, iso_date, time_slot)
        if info:
            user_name = info['name']
            user_link = f"https://vk.com/id{info['user_id']}"
            is_owner = (info['user_id'] == user_id)
            msg = f"🎲 Стол {table_num}, {date_str} ({slot_name}) уже зарезервирован.\n👤 {user_name} ({user_link})"
            waiting_for_slot_action[user_id] = {
                'table': table_num,
                'date': iso_date,
                'slot': time_slot,
                'date_str': date_str,
                'slot_name': slot_name,
                'is_occupied': True
            }
            send_message_func(vk, user_id, msg, get_reserve_table_actions_keyboard(is_reserved=True, is_owner=is_owner))
        else:
            send_message_func(vk, user_id, "❌ Ошибка: слот не найден.")
    return True

def handle_take_reserve(vk, user_id, send_message_func, admin_ids):
    """Создаёт резерв и отправляет уведомление админам"""
    if user_id not in waiting_for_slot_action:
        send_message_func(vk, user_id, "❌ Сначала выберите стол и дату.")
        return
    data = waiting_for_slot_action.pop(user_id)
    if data.get('is_occupied'):
        send_message_func(vk, user_id, "❌ Этот слот уже занят.")
        handle_reserve_menu(vk, user_id, send_message_func)
        return
    table_num = data['table']
    iso_date = data['date']
    time_slot = data['slot']
    date_str = data['date_str']
    slot_name = data['slot_name']
    if not rdb.is_slot_free(table_num, iso_date, time_slot):
        send_message_func(vk, user_id, "❌ Слот уже занят.")
        handle_reserve_menu(vk, user_id, send_message_func)
        return
    user_name = get_user_name(vk, user_id)
    rdb.create_reserve(table_num, iso_date, time_slot, user_id, user_name)
    send_message_func(vk, user_id, f"✅ Стол {table_num} зарезервирован на {date_str} ({slot_name})!")

    # Уведомляем всех администраторов (включая самого пользователя, если он админ)
    # Если не хотите отправлять самому себе, раскомментируйте проверку
    for admin_id in admin_ids:
        # if admin_id == user_id:
        #     continue   # не отправлять себе
        try:
            send_message_func(vk, admin_id,
                f"🎲 **Новый резерв стола**\n"
                f"🎲 Стол {table_num}\n"
                f"📅 {date_str} ({slot_name})\n"
                f"👤 {user_name} (https://vk.com/id{user_id})")
        except:
            pass
    handle_reserve_menu(vk, user_id, send_message_func)

def handle_cancel_reserve_from_action(vk, user_id, send_message_func):
    """Снимает резерв (без уведомления админов)"""
    if user_id not in waiting_for_slot_action:
        send_message_func(vk, user_id, "❌ Сначала выберите стол и дату.")
        return
    data = waiting_for_slot_action.get(user_id)
    if not data:
        return
    table_num = data['table']
    iso_date = data['date']
    time_slot = data['slot']
    date_str = data['date_str']
    slot_name = data['slot_name']
    info = rdb.get_reserve_info(table_num, iso_date, time_slot)
    if not info or info['user_id'] != user_id:
        send_message_func(vk, user_id, "❌ Вы не можете снять этот резерв (не владелец).")
        handle_reserve_menu(vk, user_id, send_message_func)
        return
    rdb.cancel_reserve(table_num, iso_date, time_slot)
    send_message_func(vk, user_id, f"✅ Резерв на {date_str} ({slot_name}) отменён.")
    waiting_for_slot_action.pop(user_id, None)
    handle_reserve_menu(vk, user_id, send_message_func)

def handle_view_reserve_from_action(vk, user_id, send_message_func):
    """Показывает информацию о резерве (без уведомлений)"""
    if user_id not in waiting_for_slot_action:
        send_message_func(vk, user_id, "❌ Сначала выберите стол и дату.")
        return
    data = waiting_for_slot_action.get(user_id)
    if not data:
        return
    table_num = data['table']
    iso_date = data['date']
    time_slot = data['slot']
    date_str = data['date_str']
    slot_name = data['slot_name']
    info = rdb.get_reserve_info(table_num, iso_date, time_slot)
    if info:
        user_link = f"https://vk.com/id{info['user_id']}"
        send_message_func(vk, user_id, f"🎲 Стол {table_num}, {date_str} ({slot_name})\n👤 {info['name']} ({user_link})")
    else:
        send_message_func(vk, user_id, f"❌ Резерв не найден (возможно, был отменён).")
    handle_reserve_menu(vk, user_id, send_message_func)

def is_waiting_for_reserve_table(user_id):
    return user_id in waiting_for_reserve_table