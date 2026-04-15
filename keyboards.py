# keyboards.py

from vk_api.keyboard import VkKeyboard, VkKeyboardColor


# ==================================================
# ГЛАВНОЕ МЕНЮ
# ==================================================

def get_main_keyboard():
    """Главная клавиатура бота (вертикально)"""
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('🏆 ТУРНИРЫ', color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()  
    keyboard.add_button('💰 СПОНСОР', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()  
    keyboard.add_button('🔑 КЛЮЧИ', color=VkKeyboardColor.SECONDARY)
    return keyboard


# ==================================================
# ТУРНИРЫ - ВЕТКА 1: ГЛАВНОЕ МЕНЮ ТУРНИРОВ
# ==================================================

def get_tournament_keyboard(is_admin=False):
    """
    Клавиатура раздела ТУРНИРЫ (после нажатия на главную кнопку)
    - Список турниров: бот показывает список, ждет номер
    - Управление турнирами: для админа (создание/удаление)
    """
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('📋 Список турниров', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    if is_admin:
        keyboard.add_button('➕ Управление турнирами', color=VkKeyboardColor.POSITIVE)
        keyboard.add_line()
    keyboard.add_button('🔙 Назад', color=VkKeyboardColor.NEGATIVE)
    return keyboard


# ==================================================
# ТУРНИРЫ - ВЕТКА 2: УПРАВЛЕНИЕ ТУРНИРАМИ (АДМИН)
# ==================================================

def get_tournament_user_keyboard(is_admin=False):
    """
    Клавиатура для управления турнирами (выбор, создание, удаление)
    - Выбрать турнир: бот показывает список, ждет номер выбранного турнира
    - Создать турнир: для админа
    - Удалить турнир: для админа (после выбора турнира)
    """
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('📋 Выбрать турнир', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    if is_admin:
        keyboard.add_button('➕ Создать турнир', color=VkKeyboardColor.POSITIVE)
        keyboard.add_line()
        keyboard.add_button('🗑️ Удалить турнир', color=VkKeyboardColor.NEGATIVE)
        keyboard.add_line()
    keyboard.add_button('🔙 Назад', color=VkKeyboardColor.NEGATIVE)
    return keyboard


# ==================================================
# ТУРНИРЫ - ВЕТКА 3: ДЕЙСТВИЯ С ВЫБРАННЫМ ТУРНИРОМ
# ==================================================

def get_tournament_actions_keyboard(registered=False, is_admin=False):
    """
    Клавиатура действий для выбранного турнира
    - Для незарегистрированных: только регистрация
    - Для зарегистрированных: редактирование, оплата, начало, список игроков
    - Для админа: дополнительная кнопка управления игроками
    """
    keyboard = VkKeyboard(one_time=False)
    if not registered:
        keyboard.add_button('📝 Зарегистрироваться', color=VkKeyboardColor.POSITIVE)
    else:
        keyboard.add_button('✏️ Редактировать мои данные', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('💳 Внести оплату', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    if is_admin:
        # Админ видит кнопку "Начать турнир"
        keyboard.add_button('▶️ Начать турнир', color=VkKeyboardColor.POSITIVE)
    else:
        # Для игроков – кнопка "Сдать результат" (или "Начать матч")
        keyboard.add_button('🎮 Сдать результат', color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button('👥 Список игроков', color=VkKeyboardColor.SECONDARY)
    if is_admin:
        keyboard.add_line()
        keyboard.add_button('⚙️ Управление игроками', color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button('🔙 Назад', color=VkKeyboardColor.NEGATIVE)
    return keyboard

# ==================================================
# ТУРНИРЫ - ВЕТКА 4: УПРАВЛЕНИЕ ИГРОКАМИ (АДМИН)
# ==================================================

def get_players_menu_keyboard(is_admin=False):
    """
    Клавиатура подменю Игроки (для админа)
    - Показать список игроков
    - Удалить игрока
    - Создать пары
    - Редактировать пару
    - Действия с турниром
    """
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('📋 Показать список игроков', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    if is_admin:
        keyboard.add_button('🗑️ Удалить игрока', color=VkKeyboardColor.NEGATIVE)
        keyboard.add_line()
        keyboard.add_button('🔗 Создать пары', color=VkKeyboardColor.POSITIVE)
        keyboard.add_line()
        keyboard.add_button('📢 Сообщение о туре', color=VkKeyboardColor.PRIMARY)  
        keyboard.add_line()
        keyboard.add_button('🏁 Завершить турнир', color=VkKeyboardColor.NEGATIVE)  
        keyboard.add_line()
        keyboard.add_button('⚙️ Действия с турниром', color=VkKeyboardColor.SECONDARY)
        keyboard.add_line()
    keyboard.add_button('🔙 Назад', color=VkKeyboardColor.NEGATIVE)
    return keyboard


# ==================================================
# ТУРНИРЫ - ВЕТКА 5: ДЕЙСТВИЯ С ТУРНИРОМ (АДМИН)
# ==================================================

def get_event_actions_menu_keyboard():
    """
    Клавиатура подменю Действия с турниром (для админа)
    - Показать игрокам пары
    - Показать таблицу лидеров
    - Редактировать таблицу лидеров
    """
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('📨 Показать игрокам пары', color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button('🏆 Показать таблицу лидеров', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('✏️ Редактировать таблицу лидеров', color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button('🔙 Назад', color=VkKeyboardColor.NEGATIVE)
    return keyboard


# ==================================================
# СПОНСОРЫ
# ==================================================

def get_sponsor_keyboard():
    """Клавиатура раздела СПОНСОР"""
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('💰 Стать спонсором', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('✅ Подтвердить оплату', color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button('❌ Отписаться', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button('🔙 Назад', color=VkKeyboardColor.SECONDARY)
    return keyboard


# ==================================================
# КЛЮЧИ
# ==================================================

def get_key_keyboard():
    """Клавиатура раздела КЛЮЧИ"""
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('🔑 Взять ключ', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('🔓 Отдать ключ', color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button('❓ Кто держит ключ', color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button('🔙 Назад', color=VkKeyboardColor.NEGATIVE)
    return keyboard



# ==================================================
# СПОНСОРЫ
# ==================================================

def get_sponsor_keyboard(is_sponsor=False, is_admin=False):
    """
    Клавиатура раздела СПОНСОР
    - Для обычного пользователя: стать спонсором / подтвердить оплату / отписаться / назад
    - Для админа: дополнительная кнопка "Напомнить об оплате" и "Показать список"
    """
    keyboard = VkKeyboard(one_time=False)
    if not is_sponsor:
        keyboard.add_button('💰 Стать спонсором', color=VkKeyboardColor.PRIMARY)
    else:
        keyboard.add_button('✅ Подтвердить оплату', color=VkKeyboardColor.POSITIVE)
        keyboard.add_line()
        keyboard.add_button('❌ Отписаться', color=VkKeyboardColor.NEGATIVE)
    if is_admin:
        keyboard.add_line()
        keyboard.add_button('📢 Напомнить об оплате', color=VkKeyboardColor.SECONDARY)
        keyboard.add_line()
        keyboard.add_button('📋 Показать список спонсоров', color=VkKeyboardColor.PRIMARY)
        keyboard.add_line()
        keyboard.add_button('🔄 Сбросить месячные суммы', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button('🔙 Назад', color=VkKeyboardColor.NEGATIVE)
    return keyboard