# keyboards_event.py
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

def get_events_main_keyboard(is_admin=False):
    keyboard = VkKeyboard(one_time=False)
    if is_admin:
        keyboard.add_button('➕ Создать мероприятие', color=VkKeyboardColor.POSITIVE)
        keyboard.add_line()
        keyboard.add_button('🗑️ Удалить мероприятие', color=VkKeyboardColor.NEGATIVE)
        keyboard.add_line()
    keyboard.add_button('📋 Список мероприятий', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('🔙 Назад', color=VkKeyboardColor.NEGATIVE)
    return keyboard

def get_events_list_keyboard(events):
    keyboard = VkKeyboard(one_time=False)
    for ev in events:
        keyboard.add_button(ev['name'], color=VkKeyboardColor.PRIMARY)
        keyboard.add_line()
    keyboard.add_button('🔙 Назад', color=VkKeyboardColor.NEGATIVE)
    return keyboard

def get_event_actions_keyboard(is_admin=False):
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('📝 Зарегистрироваться', color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button('❌ Отказаться от участия', color=VkKeyboardColor.NEGATIVE)   # уникальное название
    keyboard.add_line()
    keyboard.add_button('💳 Оплатить', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('📋 Посмотреть участников', color=VkKeyboardColor.SECONDARY)   # уникальное название
    if is_admin:
        keyboard.add_line()
        keyboard.add_button('⚠️ Удалить участника (админ)', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button('🔙 Назад', color=VkKeyboardColor.SECONDARY)
    return keyboard