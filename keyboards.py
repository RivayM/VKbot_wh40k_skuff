# keyboards.py

from vk_api.keyboard import VkKeyboard, VkKeyboardColor


def get_main_keyboard():
    """Главная клавиатура бота (вертикально)"""
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('🏆 ТУРНИРЫ', color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()  # <-- перевод строки
    keyboard.add_button('💰 СПОНСОР', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()  # <-- перевод строки
    keyboard.add_button('🔑 КЛЮЧИ', color=VkKeyboardColor.SECONDARY)
    return keyboard


def get_tournament_keyboard():
    """Клавиатура раздела ТУРНИРЫ (вертикально)"""
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('📝 Зарегистрироваться', color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button('📊 Сдать результат', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('🔙 Назад', color=VkKeyboardColor.NEGATIVE)
    return keyboard


def get_sponsor_keyboard():
    """Клавиатура раздела СПОНСОР (вертикально)"""
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('💰 Стать спонсором', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('✅ Подтвердить оплату', color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button('❌ Отписаться', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button('🔙 Назад', color=VkKeyboardColor.SECONDARY)
    return keyboard


def get_key_keyboard():
    """Клавиатура раздела КЛЮЧИ (вертикально)"""
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('🔑 Взять ключ', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('🔓 Отдать ключ', color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button('❓ Кто держит ключ', color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button('🔙 Назад', color=VkKeyboardColor.NEGATIVE)
    return keyboard