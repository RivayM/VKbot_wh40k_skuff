import vk_api
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from database.db import add_sponsor, get_sponsor
from keyboards.keyboards import get_main_keyboard, get_sponsor_keyboard, get_confirmation_keyboard

# Хранилище временных данных (ожидание ввода имени)
waiting_for_name = {}

def handle_start(bot, vk, event):
    """Обработка начала диалога"""
    user_id = event.user_id
    

    sponsor = get_sponsor(user_id)
    
    if sponsor and sponsor['status'] == 'active':
        # Уже спонсор
        vk.messages.send(
            user_id=user_id,
            message="Вы уже являетесь спонсором клуба!",
            keyboard=get_sponsor_keyboard().get_keyboard(),
            random_id=0
        )
    else:
        vk.messages.send(
            user_id=user_id,
            message="Добро пожаловать!\n\n💰 Нажмите кнопку, чтобы стать спонсором клуба:",
            keyboard=get_main_keyboard().get_keyboard(),
            random_id=0
        )

def handle_become_sponsor(bot, vk, event):
    """Начало регистрации спонсора"""
    user_id = event.user_id
    
    # Проверяем, не спонсор ли уже
    sponsor = get_sponsor(user_id)
    if sponsor and sponsor['status'] == 'active':
        vk.messages.send(
            user_id=user_id,
            message="Вы уже являетесь спонсором!",
            keyboard=get_sponsor_keyboard().get_keyboard(),
            random_id=0
        )
        return
    
    # Запрашиваем имя
    waiting_for_name[user_id] = True
    vk.messages.send(
        user_id=user_id,
        message="Введите ваше имя (как вы хотите, чтобы вас называли):",
        random_id=0
    )

def handle_name_input(vk, event, text):
    """Обработка ввода имени"""
    user_id = event.user_id
    name = text.strip()
    
    if len(name) > 50:
        vk.messages.send(
            user_id=user_id,
            message="Имя слишком длинное. Пожалуйста, введите имя покороче (до 50 символов):",
            random_id=0
        )
        return
    
    # Сохраняем спонсора
    add_sponsor(user_id, name)
    
    # Удаляем из ожидания
    if user_id in waiting_for_name:
        del waiting_for_name[user_id]
    
    # Отправляем подтверждение
    vk.messages.send(
        user_id=user_id,
        message=f"✅ Отлично, {name}! Вы зарегистрированы как спонсор клуба!\n\nТеперь вы можете подтвердить оплату, нажав кнопку ниже.",
        keyboard=get_sponsor_keyboard().get_keyboard(),
        random_id=0
    )