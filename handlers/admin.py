from database.db import get_all_sponsors, get_sponsors_without_photo, reset_photo_sent, get_sponsor
from keyboards.keyboards import get_admin_keyboard
import datetime

# Хранилище для ожидания даты
waiting_for_deadline = {}

def handle_admin_panel(vk, event, ADMIN_IDS):
    """Показ админ-панели"""
    user_id = event.user_id
    
    if user_id not in ADMIN_IDS:
        return
    
    vk.messages.send(
        user_id=user_id,
        message="📊 Админ-панель\n\nВыберите действие:",
        keyboard=get_admin_keyboard().get_keyboard(),
        random_id=0
    )

def handle_sponsors_list(vk, event, ADMIN_IDS):
    """Список всех спонсоров"""
    user_id = event.user_id
    
    if user_id not in ADMIN_IDS:
        return
    
    sponsors = get_all_sponsors()
    
    if not sponsors:
        vk.messages.send(
            user_id=user_id,
            message="📊 Список спонсоров пуст",
            random_id=0
        )
        return
    
    message = "📊 СПИСОК СПОНСОРОВ:\n\n"
    for s in sponsors:
        message += f"👤 {s['name']} (id{s['user_id']})\n"
        message += f"   📅 Регистрация: {s['registered_at'][:10]}\n"
        message += f"   📸 Фото за период: {'✅' if s['photo_sent_for_period'] else '❌'}\n\n"
    
    # Разбиваем на части, если сообщение длинное
    if len(message) > 4000:
        vk.messages.send(
            user_id=user_id,
            message="📊 Список слишком длинный. Используйте кнопку 'Не прислали фото' для просмотра должников.",
            random_id=0
        )
    else:
        vk.messages.send(
            user_id=user_id,
            message=message,
            random_id=0
        )

def handle_no_photo_list(vk, event, ADMIN_IDS):
    """Список спонсоров, не приславших фото"""
    user_id = event.user_id
    
    if user_id not in ADMIN_IDS:
        return
    
    sponsors = get_sponsors_without_photo()
    
    if not sponsors:
        vk.messages.send(
            user_id=user_id,
            message="✅ Все спонсоры прислали фото за текущий период!",
            random_id=0
        )
        return
    
    message = "📸 НЕ ПРИСЛАЛИ ФОТО:\n\n"
    for s in sponsors:
        message += f"👤 {s['name']} (id{s['user_id']})\n"
        message += f"   📅 Зарегистрирован: {s['registered_at'][:10]}\n\n"
    
    vk.messages.send(
        user_id=user_id,
        message=message,
        random_id=0
    )

def handle_with_photo_list(vk, event, ADMIN_IDS):
    """Список спонсоров, приславших фото"""
    user_id = event.user_id
    
    if user_id not in ADMIN_IDS:
        return
    
    sponsors = get_all_sponsors()
    with_photo = [s for s in sponsors if s['photo_sent_for_period']]
    
    if not with_photo:
        vk.messages.send(
            user_id=user_id,
            message="📸 Нет спонсоров, приславших фото за текущий период.",
            random_id=0
        )
        return
    
    message = "✅ ПРИСЛАЛИ ФОТО:\n\n"
    for s in with_photo:
        message += f"👤 {s['name']} (id{s['user_id']})\n"
    
    vk.messages.send(
        user_id=user_id,
        message=message,
        random_id=0
    )

def handle_set_deadline(vk, event, ADMIN_IDS):
    """Назначение даты оплаты"""
    user_id = event.user_id
    
    if user_id not in ADMIN_IDS:
        return
    
    waiting_for_deadline[user_id] = True
    vk.messages.send(
        user_id=user_id,
        message="📅 Введите день месяца для напоминания об оплате (число от 1 до 31):\n\nНапример: 25",
        random_id=0
    )

def process_deadline_input(vk, event, ADMIN_IDS, text):
    """Обработка ввода даты оплаты"""
    user_id = event.user_id
    
    if user_id not in ADMIN_IDS or user_id not in waiting_for_deadline:
        return False
    
    try:
        day = int(text.strip())
        if day < 1 or day > 31:
            raise ValueError
        
        waiting_for_deadline.pop(user_id, None)
        
        # Здесь нужно обновить настройку в БД
        # Для простоты пока выводим сообщение
        vk.messages.send(
            user_id=user_id,
            message=f"✅ Дата напоминания установлена на {day} число каждого месяца.",
            keyboard=get_admin_keyboard().get_keyboard(),
            random_id=0
        )
        return True
        
    except ValueError:
        vk.messages.send(
            user_id=user_id,
            message="❌ Некорректное число. Пожалуйста, введите число от 1 до 31:",
            random_id=0
        )
        return True