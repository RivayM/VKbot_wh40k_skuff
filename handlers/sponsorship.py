import logging
from database import (
    add_sponsor, get_sponsor, remove_sponsor, 
    update_payment_date, is_sponsor, get_sponsor_days
)
from keyboards import get_main_keyboard, get_sponsor_keyboard
from utils.helpers import extract_photo_url, send_message

logger = logging.getLogger(__name__)

# Хранилища состояний
waiting_for_name = {}
waiting_for_photo = {}
waiting_for_unsubscribe = {}

# handlers/sponsorship.py

def handle_start(vk, user_id, send_message_func):
    """Обработчик команды /start и кнопки Начать"""
    from database import is_sponsor, get_sponsor_days
    from keyboards import get_main_keyboard
    
    if is_sponsor(user_id):
        days_count = get_sponsor_days(user_id)
        send_message_func(vk, user_id, 
            f"🏠 С возвращением!\n\nВы спонсор уже {days_count} дней! 🙏", 
            get_main_keyboard())
    else:
        send_message_func(vk, user_id, 
            "🏠 Добро пожаловать!\n\nЯ бот для управления турнирами, спонсорами и ключами.\n\n"
            "Выберите раздел в меню ниже:", 
            get_main_keyboard())

def handle_sponsor_menu(vk, user_id, send_msg_func):
    """Обработка кнопки 'Спонсор'"""
    logger.info(f"🔹 Меню спонсора для {user_id}")
    
    if is_sponsor(user_id):
        days_count = get_sponsor_days(user_id)
        send_msg_func(vk, user_id, 
            f"💰 Меню спонсора\n\n"
            f"Вы поддерживаете клуб уже {days_count} дней! 🙏\n\n"
            f"Выберите действие:", 
            get_sponsor_keyboard())
    else:
        waiting_for_name[user_id] = True
        send_msg_func(vk, user_id, "📝 Введите ваше имя (как вы хотите, чтобы вас называли):")

def handle_name_input(vk, user_id, text, send_msg_func):
    """Обработка ввода имени"""
    if user_id not in waiting_for_name:
        return False
    
    name = text.strip()
    if len(name) > 50:
        send_msg_func(vk, user_id, "❌ Имя слишком длинное. Введите короче:")
        return True
    
    add_sponsor(user_id, name)
    del waiting_for_name[user_id]
    send_msg_func(vk, user_id, f"✅ Отлично, {name}! Вы зарегистрированы как спонсор!", get_sponsor_keyboard())
    return True

def handle_payment_request(vk, user_id, send_msg_func):
    """Обработка кнопки 'Подтвердить оплату'"""
    logger.info(f"🔹 Подтверждение оплаты для {user_id}")
    if not is_sponsor(user_id):
        send_msg_func(vk, user_id, "❌ Вы не зарегистрированы как спонсор.")
        return
    
    if user_id in waiting_for_photo:
        send_msg_func(vk, user_id, "📸 Вы уже в режиме отправки фото.\n\nНажмите 'Назад', чтобы отменить.")
    else:
        waiting_for_photo[user_id] = True
        send_msg_func(vk, user_id, "📸 Отправьте фото подтверждения оплаты:\n\n(нажмите 'Назад', чтобы отменить)")

def handle_photo_input(vk, user_id, attachments, ADMIN_IDS, send_msg_func):
    """Обработка отправки фото"""
    if user_id not in waiting_for_photo:
        return False
    
    if not attachments:
        # Не отправляем сообщение, просто ждём фото
        return True
    
    photo_url = extract_photo_url(attachments)
    
    if photo_url:
        update_payment_date(user_id)
        del waiting_for_photo[user_id]
        
        # Отправляем подтверждение пользователю
        send_msg_func(vk, user_id, 
            f"✅ Спасибо за поддержку клуба! 🙏\n\n"
            f"Ваш вклад помогает нам развиваться!", 
            get_sponsor_keyboard())
        
        # Отправляем фото ТОЛЬКО админу
        sponsor = get_sponsor(user_id)
        sponsor_name = sponsor['name'] if sponsor else f"id{user_id}"
        
        for admin_id in ADMIN_IDS:
            # Отправляем админу ссылку на фото
            send_msg_func(vk, admin_id, 
                f"📸 НОВАЯ ОПЛАТА!\n\n"
                f"👤 Спонсор: {sponsor_name}\n"
                f"🆔 ID: {user_id}\n"
                f"🔗 Ссылка на фото: {photo_url}")
        
        logger.info(f"✅ Оплата подтверждена для {user_id}")
    else:
        send_msg_func(vk, user_id, "❌ Не удалось обработать фото. Попробуйте еще раз.")
    
    return True

def handle_cancel_photo(vk, user_id, send_msg_func):
    """Отмена ожидания фото (кнопка 'Назад')"""
    if user_id in waiting_for_photo:
        del waiting_for_photo[user_id]
        send_msg_func(vk, user_id, "✅ Отправка фото отменена.", get_sponsor_keyboard())
        return True
    return False

def handle_unsubscribe(vk, user_id, send_msg_func):
    """Обработка кнопки 'Отписаться'"""
    logger.info(f"🔹 Отписка для {user_id}")
    if not is_sponsor(user_id):
        send_msg_func(vk, user_id, "❌ Вы не являетесь спонсором.")
        return
    
    waiting_for_unsubscribe[user_id] = True
    send_msg_func(vk, user_id, "⚠️ Вы уверены, что хотите отписаться?\n\nНапишите 'Да' или 'Нет'.")

def handle_unsubscribe_confirm(vk, user_id, text, send_msg_func):
    """Подтверждение отписки"""
    if user_id not in waiting_for_unsubscribe:
        return False
    
    if text.lower() == "да":
        remove_sponsor(user_id)
        del waiting_for_unsubscribe[user_id]
        send_msg_func(vk, user_id, "❌ Вы отписались от спонсорства.", get_main_keyboard())
    elif text.lower() == "нет":
        del waiting_for_unsubscribe[user_id]
        send_msg_func(vk, user_id, "✅ Действие отменено.", get_sponsor_keyboard())
    else:
        send_msg_func(vk, user_id, "Ответьте 'Да' или 'Нет'.")
    
    return True

def handle_back(vk, user_id, send_msg_func):
    """Обработка кнопки 'Назад'"""
    # Сначала проверяем, не ждёт ли пользователь фото
    if handle_cancel_photo(vk, user_id, send_msg_func):
        return
    
    # Если не ждёт фото, просто показываем главное меню
    if is_sponsor(user_id):
        days_count = get_sponsor_days(user_id)
        send_msg_func(vk, user_id, 
            f"Главное меню\n\nВы спонсор уже {days_count} дней! 🙏", 
            get_main_keyboard())
    else:
        send_msg_func(vk, user_id, "Главное меню:", get_main_keyboard())

# Функции для проверки состояний
def is_waiting_for_name(user_id):
    return user_id in waiting_for_name

def is_waiting_for_photo(user_id):
    return user_id in waiting_for_photo

def is_waiting_for_unsubscribe(user_id):
    return user_id in waiting_for_unsubscribe