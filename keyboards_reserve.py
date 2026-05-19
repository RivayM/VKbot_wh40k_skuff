# keyboards_reserve.py
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

def get_reserve_main_keyboard(tables_status):
    """
    Клавиатура со списком столов (2 кнопки в строке)
    tables_status: dict {table_number: bool} (True - зарезервирован, False - свободен)
    """
    keyboard = VkKeyboard(one_time=False)
    # Столы 1 и 2 в одной строке
    color1 = VkKeyboardColor.NEGATIVE if tables_status.get(1, False) else VkKeyboardColor.PRIMARY
    keyboard.add_button(f'🎲 Стол 1', color=color1)
    color2 = VkKeyboardColor.NEGATIVE if tables_status.get(2, False) else VkKeyboardColor.PRIMARY
    keyboard.add_button(f'🎲 Стол 2', color=color2)
    keyboard.add_line()
    # Столы 3 и 4
    color3 = VkKeyboardColor.NEGATIVE if tables_status.get(3, False) else VkKeyboardColor.PRIMARY
    keyboard.add_button(f'🎲 Стол 3', color=color3)
    color4 = VkKeyboardColor.NEGATIVE if tables_status.get(4, False) else VkKeyboardColor.PRIMARY
    keyboard.add_button(f'🎲 Стол 4', color=color4)
    keyboard.add_line()
    keyboard.add_button('🔙 Назад', color=VkKeyboardColor.NEGATIVE)
    return keyboard

def get_reserve_table_actions_keyboard(is_reserved=False, is_owner=False):
    """
    Клавиатура действий для выбранного стола
    is_reserved - зарезервирован ли стол
    is_owner   - является ли текущий пользователь тем, кто зарезервировал (или админ)
    """
    keyboard = VkKeyboard(one_time=False)
    if not is_reserved:
        keyboard.add_button('📝 Зарезервировать', color=VkKeyboardColor.POSITIVE)
    else:
        if is_owner:
            keyboard.add_button('❌ Снять резерв', color=VkKeyboardColor.NEGATIVE)
        keyboard.add_button('👥 Просмотреть резерв', color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button('🔙 Назад', color=VkKeyboardColor.NEGATIVE)
    return keyboard