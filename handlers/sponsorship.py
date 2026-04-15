# handlers/sponsorship.py

import logging
import time
from datetime import datetime
from database import (
    add_sponsor, get_sponsor, remove_sponsor, 
    update_payment_date, is_sponsor, get_sponsor_days, get_all_sponsors
)
from keyboards import get_main_keyboard, get_sponsor_keyboard
from utils.helpers import extract_photo_url, send_message
from config import PAYMENT_DEADLINE_DAY

logger = logging.getLogger(__name__)

# Хранилища состояний
waiting_for_name = {}
waiting_for_photo = {}
waiting_for_unsubscribe = {}
waiting_for_payment_amount = {}
waiting_for_payment_photo = {}


def handle_start(vk, user_id, send_message_func):
    """Обработчик команды /start"""
    if is_sponsor(user_id):
        days_count = get_sponsor_days(user_id)
        send_message_func(vk, user_id, 
            f"🏠 С возвращением!\n\nВы спонсор уже {days_count} дней! 🙏", 
            get_main_keyboard())
    else:
        send_message_func(vk, user_id, 
            "🏠 Добро пожаловать!\n\nВыберите раздел в меню ниже:", 
            get_main_keyboard())


def handle_become_sponsor(vk, user_id, send_message_func, is_admin=False):
    if is_sponsor(user_id):
        send_message_func(vk, user_id, "❌ Вы уже являетесь спонсором.", 
                         get_sponsor_keyboard(is_sponsor=True, is_admin=is_admin))
        return
    waiting_for_name[user_id] = True
    send_message_func(vk, user_id, "📝 Введите ваше имя:")

def handle_name_input(vk, user_id, text, send_msg_func, is_admin=False):
    if user_id not in waiting_for_name:
        return False
    name = text.strip()
    if len(name) > 50:
        send_msg_func(vk, user_id, "❌ Имя слишком длинное. Введите короче:")
        return True
    add_sponsor(user_id, name)
    del waiting_for_name[user_id]
    send_msg_func(vk, user_id, f"✅ Отлично, {name}! Вы зарегистрированы как спонсор!",
                  get_sponsor_keyboard(is_sponsor=True, is_admin=is_admin))
    return True


def handle_payment_request(vk, user_id, send_message_func):
    """Начинает процесс оплаты: сначала сумма, потом фото"""
    if not is_sponsor(user_id):
        send_message_func(vk, user_id, "❌ Вы не зарегистрированы как спонсор.")
        return
    waiting_for_payment_amount[user_id] = {'timestamp': time.time()}
    send_message_func(vk, user_id, "💵 Введите сумму оплаты (например, 500):\n(нажмите 'Назад', чтобы отменить)")


def handle_payment_amount(vk, user_id, text, send_message_func):
    if user_id not in waiting_for_payment_amount:
        return False
    try:
        amount = float(text.strip())
        if amount <= 0:
            raise ValueError
        waiting_for_payment_amount[user_id] = {'amount': amount, 'timestamp': time.time()}
        # Переходим в режим ожидания любого сообщения (фото или текст)
        waiting_for_payment_photo[user_id] = {'amount': amount, 'timestamp': time.time()}
        send_message_func(vk, user_id, f"💰 Сумма {amount} руб.\n\n📸 Теперь пришлите фото подтверждения (или просто напишите 'да'):")
        return True
    except ValueError:
        send_message_func(vk, user_id, "❌ Введите корректную сумму (цифрами).")
        return True

def handle_payment_photo(vk, user_id, attachments, send_message_func, admin_ids, is_admin=False):
    if user_id not in waiting_for_payment_photo:
        return False
    data = waiting_for_payment_photo.pop(user_id)
    photo_url = extract_photo_url(attachments) if attachments else None
    update_payment_date(user_id)
    if photo_url:
        send_message_func(vk, user_id, f"✅ Спасибо за оплату {data['amount']} руб.! Фото получено. 🙏",
                         get_sponsor_keyboard(is_sponsor=True, is_admin=is_admin))
    else:
        send_message_func(vk, user_id, f"✅ Спасибо за оплату {data['amount']} руб.! (фото не приложено, но мы засчитали)",
                         get_sponsor_keyboard(is_sponsor=True, is_admin=is_admin))
    # Уведомляем админов
    sponsor = get_sponsor(user_id)
    if sponsor:
        sponsor_name = sponsor.get('name', f"id{user_id}")
    else:
        sponsor_name = f"id{user_id}"
    for admin_id in admin_ids:
        try:
            msg = f"💸 **Новая оплата спонсора**\n👤 {sponsor_name}\n🆔 {user_id}\n💰 {data['amount']} руб."
            if photo_url:
                msg += f"\n🔗 Фото: {photo_url}"
            else:
                msg += "\n⚠️ Фото не приложено"
            send_message_func(vk, admin_id, msg)
        except:
            pass
    return True


def handle_unsubscribe_confirm(vk, user_id, text, send_message_func, is_admin=False):
    if user_id not in waiting_for_unsubscribe:
        return False
    if text.lower() == "да":
        remove_sponsor(user_id)
        del waiting_for_unsubscribe[user_id]
        send_message_func(vk, user_id, "❌ Вы отписались от спонсорства.", get_main_keyboard())
    elif text.lower() == "нет":
        del waiting_for_unsubscribe[user_id]
        send_message_func(vk, user_id, "✅ Действие отменено.", 
                         get_sponsor_keyboard(is_sponsor=True, is_admin=is_admin))
    else:
        send_message_func(vk, user_id, "Ответьте 'Да' или 'Нет'.")
    return True


def handle_show_sponsors(vk, user_id, send_message_func, is_admin=False):
    if not is_admin:
        send_message_func(vk, user_id, "❌ Только для администраторов.")
        return
    sponsors = get_all_sponsors()
    if not sponsors:
        send_message_func(vk, user_id, "📋 Нет зарегистрированных спонсоров.")
        return
    text = "📋 СПОНСОРЫ:\n\n"
    for s in sponsors:
        # s - это словарь
        name = s.get('name', f"id{s['user_id']}")
        last_payment = s.get('last_payment')
        paid = "✅ оплатил" if last_payment else "❌ не оплатил"
        text += f"{name} (id{s['user_id']}) — {paid}\n"
    send_message_func(vk, user_id, text)

def handle_remind_payment(vk, user_id, send_message_func, is_admin=False):
    if not is_admin:
        send_message_func(vk, user_id, "❌ Только для администраторов.")
        return
    sponsors = get_all_sponsors()
    reminded = 0
    for s in sponsors:
        last_payment = s.get('last_payment')
        if not last_payment:
            try:
                user_id_sp = s['user_id']
                name = s.get('name', f"id{user_id_sp}")
                send_message_func(vk, user_id_sp, 
                    f"📢 Уважаемый {name}! Напоминаем о необходимости оплаты.")
                reminded += 1
            except Exception as e:
                print(f"Ошибка отправки напоминания: {e}")
    send_message_func(vk, user_id, f"✅ Напоминания отправлены {reminded} спонсорам.")

def handle_cancel_payment(vk, user_id, send_message_func, is_admin=False):
    if user_id in waiting_for_payment_amount:
        del waiting_for_payment_amount[user_id]
        send_message_func(vk, user_id, "✅ Ввод суммы отменён.", get_sponsor_keyboard(is_sponsor=True, is_admin=is_admin))
        return True
    if user_id in waiting_for_payment_photo:
        del waiting_for_payment_photo[user_id]
        send_message_func(vk, user_id, "✅ Отправка фото отменена.", get_sponsor_keyboard(is_sponsor=True, is_admin=is_admin))
        return True
    return False


def is_waiting_for_name(user_id):
    return user_id in waiting_for_name


def is_waiting_for_photo(user_id):
    return user_id in waiting_for_photo


def is_waiting_for_unsubscribe(user_id):
    return user_id in waiting_for_unsubscribe