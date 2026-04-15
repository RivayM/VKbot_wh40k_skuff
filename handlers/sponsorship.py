# handlers/sponsorship.py

import logging
import time
from datetime import datetime
from database import (
    add_sponsor, get_sponsor, remove_sponsor, 
    update_payment_date, is_sponsor, get_sponsor_days, 
    get_all_sponsors,
    reset_monthly_amounts
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
waiting_for_reset_confirm = {}



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
    """Начинает процесс оплаты (запрашивает сумму)"""
    if not is_sponsor(user_id):
        send_message_func(vk, user_id, "❌ Вы не зарегистрированы как спонсор.")
        return
    waiting_for_payment_amount[user_id] = {'timestamp': time.time()}
    send_message_func(vk, user_id, "💵 Введите сумму оплаты (например, 500):\n(нажмите 'Назад', чтобы отменить)")

def handle_payment_amount(vk, user_id, text, send_message_func, is_admin=False, admin_ids=None):
    if user_id not in waiting_for_payment_amount:
        return False
    try:
        amount = float(text.strip())
        if amount <= 0:
            raise ValueError
        del waiting_for_payment_amount[user_id]
        update_payment_date(user_id, amount)
        send_message_func(vk, user_id, f"✅ Спасибо за оплату {amount} руб.! 🙏",
                         get_sponsor_keyboard(is_sponsor=True, is_admin=is_admin))
        # Уведомляем админов
        sponsor = get_sponsor(user_id)
        sponsor_name = sponsor['name'] if sponsor else f"id{user_id}"
        if admin_ids is None:
            admin_ids = []
        for admin_id in admin_ids:
            try:
                send_message_func(vk, admin_id,
                    f"💸 **Новая оплата спонсора**\n👤 {sponsor_name}\n🆔 {user_id}\n💰 {amount} руб.")
            except:
                pass
        return True
    except ValueError:
        send_message_func(vk, user_id, "❌ Введите корректную сумму (цифрами).")
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
    text = "📋 СПОНСОРЫ (сумма за текущий месяц):\n\n"
    total_sum = 0
    for s in sponsors:
        name = s['name']
        user_id_sp = s['user_id']
        monthly = s.get('monthly_amount', 0) or 0
        if monthly > 0:
            text += f"{name} (id{user_id_sp}) — ✅ оплатил {monthly} руб.\n"
            total_sum += monthly
        else:
            text += f"{name} (id{user_id_sp}) — ❌ не оплатил\n"
    text += f"\n💰 Общая сумма поступлений за месяц: {total_sum} руб."
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
        send_message_func(vk, user_id, "✅ Оплата отменена.", get_sponsor_keyboard(is_sponsor=True, is_admin=is_admin))
        return True
    return False


def is_waiting_for_name(user_id):
    return user_id in waiting_for_name


def is_waiting_for_photo(user_id):
    return user_id in waiting_for_photo


def is_waiting_for_unsubscribe(user_id):
    return user_id in waiting_for_unsubscribe

def handle_reset_monthly(vk, user_id, send_message_func, is_admin=False):
    if not is_admin:
        send_message_func(vk, user_id, "❌ Только для администраторов.")
        return
    waiting_for_reset_confirm[user_id] = True
    send_message_func(vk, user_id, "⚠️ Вы уверены, что хотите обнулить месячные суммы всех спонсоров?\n\nНапишите 'Да' или 'Нет'.")

def handle_reset_confirm(vk, user_id, text, send_message_func, is_admin=False):
    if user_id not in waiting_for_reset_confirm:
        return False
    del waiting_for_reset_confirm[user_id]
    if text.lower() == "да":
        reset_monthly_amounts()
        send_message_func(vk, user_id, "✅ Месячные суммы всех спонсоров обнулены.", get_sponsor_keyboard(is_sponsor=True, is_admin=is_admin))
    else:
        send_message_func(vk, user_id, "❌ Сброс отменён.", get_sponsor_keyboard(is_sponsor=True, is_admin=is_admin))
    return True