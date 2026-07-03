# keyboards_reserve.py
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import datetime
from database import reserve_db as rdb  # <-- добавьте этот импорт!

def get_reserve_date_keyboard():
    """
    Календарь на 12 дней (3 столбца, 4 строки) + кнопка Назад
    """
    keyboard = VkKeyboard(one_time=False)
    today = datetime.date.today()
    
    for i in range(12):
        date_obj = today + datetime.timedelta(days=i)
        date_str = date_obj.strftime('%d.%m')
        keyboard.add_button(date_str, color=VkKeyboardColor.PRIMARY)
        if (i + 1) % 3 == 0:
            keyboard.add_line()
    
    keyboard.add_button('🔙 Назад', color=VkKeyboardColor.NEGATIVE)
    return keyboard

def get_reserve_table_keyboard(date_str=None):
    """
    Клавиатура выбора стола и времени.
    Если передана дата (date_str), то занятые слоты будут красными.
    """
    keyboard = VkKeyboard(one_time=False)
    
    def get_color(table_num, time_slot):
        if date_str:
            is_free = rdb.is_slot_free(table_num, date_str, time_slot)
            print(f"[DEBUG] Стол {table_num}, слот {time_slot}: is_free={is_free}")
            if not is_free:
                return VkKeyboardColor.NEGATIVE  # красный, если занят
        return VkKeyboardColor.PRIMARY           # белый/синий, если свободен
    
    # ✅ ДОБАВЛЯЕМ КНОПКИ!
    # Строка 1: Стол 1 и Стол 2 (утро)
    keyboard.add_button('☀️ Стол 1', color=get_color(1, 1))
    keyboard.add_button('🌙 Стол 1', color=get_color(1, 2))
    keyboard.add_line()
    
    # Строка 2: Стол 1 и Стол 2 (вечер)
    keyboard.add_button('☀️ Стол 2', color=get_color(2, 1))
    keyboard.add_button('🌙 Стол 2', color=get_color(2, 2))
    keyboard.add_line()
    
    # Строка 3: Стол 3 и Стол 4 (утро)
    keyboard.add_button('☀️ Стол 3', color=get_color(3, 1))
    keyboard.add_button('🌙 Стол 3', color=get_color(3, 2))
    keyboard.add_line()
    
    # Строка 4: Стол 3 и Стол 4 (вечер)
    keyboard.add_button('☀️ Стол 4', color=get_color(4, 1))
    keyboard.add_button('🌙 Стол 4', color=get_color(4, 2))
    keyboard.add_line()
    
    keyboard.add_button('🔙 Назад', color=VkKeyboardColor.NEGATIVE)
    return keyboard

def get_reserve_table_actions_keyboard(is_reserved=False, is_owner=False):
    keyboard = VkKeyboard(one_time=False)
    if not is_reserved:
        keyboard.add_button('📝 Зарезервировать', color=VkKeyboardColor.POSITIVE)
    else:
        keyboard.add_button('📋 Посмотреть резерв', color=VkKeyboardColor.SECONDARY)
        if is_owner:
            keyboard.add_line()
            keyboard.add_button('❌ Снять резерв', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button('🔙 Назад', color=VkKeyboardColor.NEGATIVE)
    return keyboard