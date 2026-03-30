# handlers/key_handler.py (исправленная версия)

import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

# Московское время (UTC+3)
MOSCOW_TZ = timezone(timedelta(hours=3))

def get_moscow_time():
    """Возвращает текущее московское время"""
    return datetime.now(MOSCOW_TZ)


def get_user_display_name(vk, user_id):
    """Получает имя пользователя или ссылку на страницу"""
    try:
        user = vk.users.get(user_ids=user_id, fields=['screen_name'])[0]
        first_name = user.get('first_name', 'Пользователь')
        last_name = user.get('last_name', '')
        screen_name = user.get('screen_name', '')
        
        full_name = f"{first_name} {last_name}".strip()
        
        if screen_name:
            return f"{full_name} (https://vk.com/{screen_name})"
        else:
            return f"{full_name} (id{user_id})"
    except Exception as e:
        logger.error(f"Ошибка получения имени пользователя {user_id}: {e}")
        return f"Пользователь id{user_id}"


def handle_take_key(vk, user_id, send_message_func, admin_ids):
    """
    Обработчик кнопки "Взять ключ"
    """
    from database import take_key, has_key, get_key_holder
    
    # Получаем имя пользователя для отображения
    user_name = get_user_display_name(vk, user_id)
    
    # Пробуем взять ключ
    result = take_key(user_id, user_name)
    
    if result is None:
        # Ключ уже у этого пользователя
        send_message_func(vk, user_id, 
            "🔑 **Ключ уже у вас!**\n\n"
            "Если хотите отказаться от ключа, нажмите кнопку **«Отдать ключ»**.")
        return True
    
    elif result is True:
        # Ключ был свободен - успешно взят
        send_message_func(vk, user_id,
            "✅ **Вы успешно взяли ключ!**\n\n"
            "Теперь вы владеете ключом. Если хотите отказаться, нажмите **«Отдать ключ»**.")
        
        # Уведомляем админов (НО НЕ ЕСЛИ АДМИН ВЗЯЛ У СЕБЯ)
        moscow_time = get_moscow_time()
        for admin_id in admin_ids:
            # Пропускаем уведомление, если админ взял ключ у самого себя
            if admin_id == user_id:
                continue
            try:
                send_message_func(vk, admin_id,
                    f"🔔 **КЛЮЧ ВЗЯТ**\n\n"
                    f"👤 Пользователь: {user_name}\n"
                    f"🆔 ID: {user_id}\n"
                    f"⏰ Время: {moscow_time.strftime('%d.%m.%Y %H:%M:%S')} (МСК)\n\n"
                    f"Ключ был свободен.")
            except Exception as e:
                logger.error(f"Не удалось отправить уведомление админу {admin_id}: {e}")
        
        return True
    
    else:
        # Ключ был у другого пользователя - перехват
        old_user_id, old_user_name = result
        
        # Сообщение новому владельцу
        send_message_func(vk, user_id,
            f"✅ **Вы перехватили ключ!**\n\n"
            f"🔑 Предыдущий владелец: {old_user_name}\n\n"
            f"Теперь ключ у вас. Нажмите **«Отдать ключ»**, если хотите отказаться.")
        
        # Уведомляем предыдущего владельца (если это не тот же пользователь)
        if old_user_id != user_id:
            try:
                send_message_func(vk, old_user_id,
                    f"⚠️ **У вас забрали ключ!**\n\n"
                    f"👤 Новый владелец: {user_name}\n"
                    f"Ключ больше не у вас.")
            except Exception as e:
                logger.error(f"Не удалось уведомить старого владельца {old_user_id}: {e}")
        
        # Уведомляем админов (НО НЕ ЕСЛИ АДМИН ВЗЯЛ У СЕБЯ)
        moscow_time = get_moscow_time()
        for admin_id in admin_ids:
            # Пропускаем уведомление, если админ перехватил ключ у самого себя
            if admin_id == user_id:
                continue
            try:
                send_message_func(vk, admin_id,
                    f"🔄 **КЛЮЧ ПЕРЕХВАТЧЕН**\n\n"
                    f"📤 Отдал: {old_user_name} (id{old_user_id})\n"
                    f"📥 Взял: {user_name} (id{user_id})\n"
                    f"⏰ Время: {moscow_time.strftime('%d.%m.%Y %H:%M:%S')} (МСК)")
            except Exception as e:
                logger.error(f"Не удалось отправить уведомление админу {admin_id}: {e}")
        
        return True


def handle_return_key(vk, user_id, send_message_func, admin_ids):
    """Обработчик кнопки Отдать ключ"""
    from database import return_key, has_key, get_key_holder
    
    if not has_key(user_id):
        send_message_func(vk, user_id,
            "❌ **У вас нет ключа!**\n\n"
            "Сначала возьмите ключ кнопкой **«Взять ключ»**.")
        return True
    
    # Получаем имя пользователя для отчёта
    user_name = get_user_display_name(vk, user_id)
    
    # Освобождаем ключ
    return_key()
    
    send_message_func(vk, user_id,
        "✅ **Вы отдали ключ!**\n\n"
        "Ключ теперь свободен. Другой пользователь может его взять.")
    
    # Уведомляем админов (НО НЕ ЕСЛИ АДМИН ОТДАЛ СВОЙ КЛЮЧ)
    moscow_time = get_moscow_time()
    for admin_id in admin_ids:
        # Пропускаем уведомление, если админ отдал свой ключ
        if admin_id == user_id:
            continue
        try:
            send_message_func(vk, admin_id,
                f"🔓 **КЛЮЧ ОТДАН**\n\n"
                f"👤 Пользователь: {user_name}\n"
                f"🆔 ID: {user_id}\n"
                f"⏰ Время: {moscow_time.strftime('%d.%m.%Y %H:%M:%S')} (МСК)\n\n"
                f"Ключ теперь свободен.")
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление админу {admin_id}: {e}")
    
    return True


def handle_who_has_key(vk, user_id, send_message_func):
    """Показывает текущего владельца ключа"""
    from database import get_key_holder
    
    holder = get_key_holder()
    moscow_time = get_moscow_time()
    
    if holder:
        holder_id, holder_name = holder
        send_message_func(vk, user_id,
            f"🔑 **Текущий владелец ключа:**\n\n"
            f"{holder_name}\n\n"
            f"⏰ Время проверки: {moscow_time.strftime('%d.%m.%Y %H:%M:%S')} (МСК)\n\n"
            f"Если хотите забрать ключ, нажмите **«Взять ключ»**.")
    else:
        send_message_func(vk, user_id,
            f"🔓 **Ключ свободен!**\n\n"
            f"⏰ Время проверки: {moscow_time.strftime('%d.%m.%Y %H:%M:%S')} (МСК)\n\n"
            f"Нажмите **«Взять ключ»**, чтобы стать владельцем.")