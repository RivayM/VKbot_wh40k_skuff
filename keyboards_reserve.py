# keyboards_reserve.py
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

def get_reserve_main_keyboard(tables_status):
    keyboard = VkKeyboard(one_time=False)
    color1 = VkKeyboardColor.NEGATIVE if tables_status.get(1, False) else VkKeyboardColor.PRIMARY
    keyboard.add_button(f'🎲 Стол 1', color=color1)
    color2 = VkKeyboardColor.NEGATIVE if tables_status.get(2, False) else VkKeyboardColor.PRIMARY
    keyboard.add_button(f'🎲 Стол 2', color=color2)
    keyboard.add_line()
    color3 = VkKeyboardColor.NEGATIVE if tables_status.get(3, False) else VkKeyboardColor.PRIMARY
    keyboard.add_button(f'🎲 Стол 3', color=color3)
    color4 = VkKeyboardColor.NEGATIVE if tables_status.get(4, False) else VkKeyboardColor.PRIMARY
    keyboard.add_button(f'🎲 Стол 4', color=color4)
    keyboard.add_line()
    keyboard.add_button('🔙 Назад', color=VkKeyboardColor.NEGATIVE)
    return keyboard

def get_reserve_table_actions_keyboard(is_reserved=False, is_owner=False):
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