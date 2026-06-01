# handlers/event_handlers.py
import logging
import datetime
import time

from database.events_db import (
    add_event, get_all_events, delete_event,
    add_participant, remove_participant, get_participants, is_participant,
    set_paid   
)
from keyboards_event import (
    get_events_main_keyboard,
    get_events_list_keyboard,
    get_event_actions_keyboard
)

logger = logging.getLogger(__name__)

# Хранилища состояний (временные, для ожидания ввода)
waiting_for_event_payment = {}  # user_id -> {'event_id': int, 'timestamp': float}
waiting_for_event_name = {}      # user_id -> True
waiting_for_event_date = {}      # user_id -> {'name': name}
waiting_for_event_choice = {}    # user_id -> {'step': 'list'/'delete'/'selected', ...}
waiting_for_remove_participant = {}  # user_id -> {'event_id': ..., 'participants': [...]}

# ---------- Вспомогательные функции ----------
def get_user_name(vk, user_id):
    try:
        user = vk.users.get(user_ids=user_id)[0]
        return f"{user['first_name']} {user['last_name']}"
    except:
        return f"id{user_id}"

def delete_expired_events():
    """Принудительно удаляет просроченные мероприятия (вызывается при каждом входе в меню)"""
    get_all_events()  # эта функция сама удаляет просроченные

# ---------- Обработчики ----------
def handle_events_menu(vk, user_id, send_message_func, is_admin=False):
    delete_expired_events()
    send_message_func(vk, user_id, "📋 Меню мероприятий:", get_events_main_keyboard(is_admin=is_admin))

def handle_create_event(vk, user_id, send_message_func):
    waiting_for_event_name[user_id] = True
    send_message_func(vk, user_id, "📝 Введите название мероприятия:")

def handle_event_name_input(vk, user_id, text, send_message_func, is_admin=False):
    if user_id not in waiting_for_event_name:
        return False
    name = text.strip()
    if not name:
        send_message_func(vk, user_id, "❌ Название не может быть пустым.")
        return True
    del waiting_for_event_name[user_id]
    waiting_for_event_date[user_id] = {'name': name}
    send_message_func(vk, user_id, "📅 Введите дату мероприятия в формате ДД.ММ.ГГГГ (например: 25.05.2026):")
    return True

def handle_event_date_input(vk, user_id, text, send_message_func, is_admin=False):
    if user_id not in waiting_for_event_date:
        return False
    data = waiting_for_event_date.pop(user_id)
    try:
        event_date = datetime.datetime.strptime(text.strip(), '%d.%m.%Y').date()
        if event_date < datetime.date.today():
            send_message_func(vk, user_id, "❌ Дата не может быть в прошлом. Введите дату заново.")
            waiting_for_event_date[user_id] = data
            return True
        add_event(data['name'], user_id, event_date)
        send_message_func(vk, user_id, f"✅ Мероприятие '{data['name']}' создано на {text}!")
        handle_events_menu(vk, user_id, send_message_func, is_admin=is_admin)
    except ValueError:
        send_message_func(vk, user_id, "❌ Неверный формат даты. Используйте ДД.ММ.ГГГГ.")
        waiting_for_event_date[user_id] = data
    return True

def handle_list_events(vk, user_id, send_message_func, is_admin=False):
    events = get_all_events()
    if not events:
        send_message_func(vk, user_id, "📋 Нет мероприятий.")
        return
    waiting_for_event_choice[user_id] = {'step': 'list', 'events': events}
    send_message_func(vk, user_id, "Выберите мероприятие:", get_events_list_keyboard(events))

def handle_event_choice(vk, user_id, text, send_message_func, is_admin=False):
    if user_id not in waiting_for_event_choice:
        return False
    state = waiting_for_event_choice[user_id]
    if state['step'] != 'list':
        return False
    event = next((e for e in state['events'] if e['name'] == text), None)
    if not event:
        send_message_func(vk, user_id, "❌ Мероприятие не найдено.")
        del waiting_for_event_choice[user_id]
        return True
    waiting_for_event_choice[user_id] = {
        'step': 'selected',
        'event_id': event['id'],
        'event_name': event['name'],
        'event_date': event.get('event_date', 'дата не указана')
    }
    print(f"[DEBUG] Состояние после выбора: {waiting_for_event_choice[user_id]}")
    msg = f"Мероприятие: {event['name']}\n📅 Дата: {event['event_date']}\n\nДействия:"
    send_message_func(vk, user_id, msg, get_event_actions_keyboard(is_admin=is_admin))
    return True

def handle_event_action(vk, user_id, text, send_message_func, is_admin=False):
    print(f"[DEBUG] handle_event_action вызвана с текстом '{text}', user_id={user_id}")
    if user_id not in waiting_for_event_choice:
        print("[DEBUG] Нет waiting_for_event_choice")
        return False
    state = waiting_for_event_choice[user_id]
    print(f"[DEBUG] state = {state}")
    if state['step'] != 'selected':
        print(f"[DEBUG] step не selected, а {state['step']}")
        return False
    eid = state['event_id']
    print(f"[DEBUG] eid={eid}")
    
    if text == "📝 Зарегистрироваться":
        name = get_user_name(vk, user_id)
        print(f"[DEBUG] Регистрация: eid={eid}, user={user_id}, name={name}")
        success = add_participant(eid, user_id, name)
        print(f"[DEBUG] Успех регистрации: {success}")
        if success:
            send_message_func(vk, user_id, "✅ Вы зарегистрированы!")
        else:
            send_message_func(vk, user_id, "❌ Вы уже зарегистрированы.")
        return True
    
    elif text == "❌ Отказаться от участия":
        if remove_participant(eid, user_id):
            send_message_func(vk, user_id, "✅ Вы отказались от участия.")
        else:
            send_message_func(vk, user_id, "❌ Вы не были зарегистрированы.")
        return True
    
    elif text == "💳 Оплатить":
        if not is_participant(eid, user_id):
            send_message_func(vk, user_id, "❌ Вы не зарегистрированы на мероприятие. Сначала зарегистрируйтесь.")
            return True
        waiting_for_event_payment[user_id] = {'event_id': eid, 'timestamp': time.time()}
        print(f"[DEBUG] waiting_for_event_payment установлен: {waiting_for_event_payment}")  # добавьте
        send_message_func(vk, user_id, "💵 Введите сумму оплаты (например, 500):\n(нажмите 'Назад', чтобы отменить)")
        return True
    else:
        return False
    send_message_func(vk, user_id, f"Мероприятие: {state['event_name']}\n\nДействия:", get_event_actions_keyboard(is_admin=is_admin))
    return True

def handle_show_participants(vk, user_id, send_message_func, event_id, event_name, is_admin=False):
    participants = get_participants(event_id)
    if not participants:
        send_message_func(vk, user_id, "📋 Нет зарегистрированных участников.")
        return
    text = f"👥 Участники мероприятия '{event_name}':\n\n"
    for p in participants:
        link = f"https://vk.com/id{p['user_id']}"
        if is_admin:
            paid_status = "✅ оплатил" if p.get('paid', 0) else "❌ не оплатил"
            text += f"{p['name']} ({link}) — {paid_status}\n"
        else:
            text += f"{p['name']} ({link})\n"
    send_message_func(vk, user_id, text)

def handle_remove_participant_start(vk, user_id, send_message_func, event_id):
    print(f"[DEBUG] handle_remove_participant_start: user={user_id}, event={event_id}")
    participants = get_participants(event_id)
    print(f"[DEBUG] participants = {participants}")
    if not participants:
        print("[DEBUG] participants empty, sending 'Нет участников'")
        send_message_func(vk, user_id, "📋 Нет участников для удаления.")
        return
    text = "Выберите номер участника для удаления:\n\n"
    for idx, p in enumerate(participants, 1):
        text += f"{idx}. {p['name']} (id{p['user_id']})\n"
    waiting_for_remove_participant[user_id] = {'event_id': event_id, 'participants': participants}
    print(f"[DEBUG] waiting_for_remove_participant set: {waiting_for_remove_participant}")
    send_message_func(vk, user_id, text)
    print("[DEBUG] message sent")

def handle_remove_participant_confirm(vk, user_id, text, send_message_func):
    if user_id not in waiting_for_remove_participant:
        return False
    data = waiting_for_remove_participant.pop(user_id)
    try:
        idx = int(text.strip())
        if 1 <= idx <= len(data['participants']):
            p = data['participants'][idx-1]
            remove_participant(data['event_id'], p['user_id'])
            send_message_func(vk, user_id, f"✅ Участник {p['name']} удалён.")
        else:
            send_message_func(vk, user_id, "❌ Неверный номер.")
    except ValueError:
        send_message_func(vk, user_id, "❌ Введите номер цифрой.")
    return True

def handle_table_selection(vk, user_id, text, send_message_func):
    print(f"[DEBUG] handle_table_selection вызвана с текстом '{text}'")
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
    # Создаём клавиатуру
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
    print("[DEBUG] Отправляем клавиатуру с датами")
    send_message_func(vk, user_id, "🎲 Выберите дату и время:", keyboard)
    return True

def handle_delete_event(vk, user_id, send_message_func, is_admin=False):
    if not is_admin:
        send_message_func(vk, user_id, "❌ Только для администраторов.")
        return
    events = get_all_events()
    if not events:
        send_message_func(vk, user_id, "📋 Нет мероприятий для удаления.")
        return
    waiting_for_event_choice[user_id] = {'step': 'delete', 'events': events}
    send_message_func(vk, user_id, "Выберите мероприятие для удаления:", get_events_list_keyboard(events))

def handle_delete_choice(vk, user_id, text, send_message_func, is_admin=False):
    if user_id not in waiting_for_event_choice:
        return False
    state = waiting_for_event_choice[user_id]
    if state['step'] != 'delete':
        return False
    event = next((e for e in state['events'] if e['name'] == text), None)
    if not event:
        send_message_func(vk, user_id, "❌ Мероприятие не найдено.")
        del waiting_for_event_choice[user_id]
        return True
    delete_event(event['id'])
    send_message_func(vk, user_id, f"✅ Мероприятие '{event['name']}' удалено.")
    handle_events_menu(vk, user_id, send_message_func, is_admin=is_admin)
    del waiting_for_event_choice[user_id]
    return True

# ---------- Функции для проверки состояний ----------
def is_waiting_for_event_name(user_id):
    return user_id in waiting_for_event_name

def is_waiting_for_event_date(user_id):
    return user_id in waiting_for_event_date

def is_waiting_for_event_choice(user_id):
    return user_id in waiting_for_event_choice

def is_waiting_for_remove_participant(user_id):
    return user_id in waiting_for_remove_participant

def handle_event_payment_amount(vk, user_id, text, send_message_func, is_admin=False):
    print(f"[DEBUG] ВХОД В handle_event_payment_amount с text={text}, user={user_id}")
    if user_id not in waiting_for_event_payment:
        print("[DEBUG] Нет ожидания оплаты")
        return False
    data = waiting_for_event_payment.pop(user_id)
    try:
        amount = float(text.strip())
        if amount <= 0:
            raise ValueError
        set_paid(data['event_id'], user_id, amount)
        send_message_func(vk, user_id, f"✅ Спасибо за оплату {amount} руб.!")
        # Вернуться в меню действий
        state = waiting_for_event_choice.get(user_id)
        if state and state.get('step') == 'selected':
            send_message_func(vk, user_id, f"Мероприятие: {state['event_name']}\n\nДействия:", get_event_actions_keyboard(is_admin=is_admin))
        return True
    except ValueError:
        send_message_func(vk, user_id, "❌ Введите корректную сумму (цифрами).")
        return True