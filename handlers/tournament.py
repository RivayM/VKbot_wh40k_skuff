import logging
from database import (
    get_active_tournaments, create_tournament, complete_tournament,
    register_for_tournament, is_registered_for_tournament, get_all_tournaments
)
from keyboards import get_tournament_keyboard, get_sponsor_keyboard, get_key_keyboard, get_main_keyboard

logger = logging.getLogger(__name__)

# Хранилища состояний
waiting_for_tournament_name = {}
waiting_for_tournament_date = {}
waiting_for_tournament_reg = {}

def handle_tournament_menu(vk, user_id, is_admin, send_message):
    """Обработка кнопки 'Турнир'"""
    logger.info(f"🔹 Турнир меню для {user_id}")
    
    active_tournaments = get_active_tournaments()
    
    if active_tournaments:
        # Есть активные турниры
        tournaments_text = "📋 Активные турниры:\n\n"
        for t in active_tournaments:
            tournaments_text += f"🏆 {t['name']} ({t['date']})\n"
        
        send_message(vk, user_id, tournaments_text)
    
    if is_admin:
        send_message(vk, user_id, "⚙️ Админ-меню турниров:", get_tournament_admin_keyboard())
    else:
        send_message(vk, user_id, "🎮 Меню турниров:", get_tournament_user_keyboard())

def handle_register_for_tournament(vk, user_id, send_message):
    """Обработка кнопки 'Зарегистрироваться на турнир'"""
    logger.info(f"🔹 Регистрация на турнир для {user_id}")
    
    active_tournaments = get_active_tournaments()
    
    if not active_tournaments:
        send_message(vk, user_id, "❌ Нет активных турниров для регистрации.")
        return
    
    # Показываем список турниров
    tournaments_text = "🎯 Выберите турнир (введите номер):\n\n"
    for i, t in enumerate(active_tournaments, 1):
        tournaments_text += f"{i}. {t['name']} ({t['date']})\n"
    
    waiting_for_tournament_reg[user_id] = active_tournaments
    send_message(vk, user_id, tournaments_text)

def handle_tournament_selection(vk, user_id, text, send_message):
    """Обработка выбора турнира для регистрации"""
    if user_id not in waiting_for_tournament_reg:
        return False
    
    try:
        num = int(text)
        tournaments = waiting_for_tournament_reg[user_id]
        
        if 1 <= num <= len(tournaments):
            tournament = tournaments[num - 1]
            
            if is_registered_for_tournament(user_id, tournament['id']):
                send_message(vk, user_id, f"❌ Вы уже зарегистрированы на турнир '{tournament['name']}'")
            else:
                register_for_tournament(user_id, tournament['id'])
                send_message(vk, user_id, f"✅ Вы зарегистрированы на турнир '{tournament['name']}'!")
        else:
            send_message(vk, user_id, "❌ Неверный номер. Попробуйте еще раз.")
            return True
        
        del waiting_for_tournament_reg[user_id]
        return True
        
    except ValueError:
        send_message(vk, user_id, "❌ Введите номер турнира цифрой.")
        return True

def handle_start_tournament(vk, user_id, send_message):
    """Обработка кнопки 'Начать турнир' (только админ)"""
    logger.info(f"🔹 Админ начал создание турнира")
    waiting_for_tournament_name[user_id] = True
    send_message(vk, user_id, "📝 Введите название турнира:")

def handle_tournament_name_input(vk, user_id, text, send_message):
    """Обработка ввода названия турнира"""
    if user_id not in waiting_for_tournament_name:
        return False
    
    waiting_for_tournament_name[user_id] = text
    del waiting_for_tournament_name[user_id]
    waiting_for_tournament_date[user_id] = True
    send_message(vk, user_id, "📅 Введите дату турнира (например: 25.04.2026):")
    return True

def handle_tournament_date_input(vk, user_id, text, send_message):
    """Обработка ввода даты турнира"""
    if user_id not in waiting_for_tournament_date:
        return False
    
    name = waiting_for_tournament_date.pop(user_id)
    if isinstance(name, dict) or not name:
        return False
    
    create_tournament(name, text)
    send_message(vk, user_id, f"✅ Турнир '{name}' создан на {text}!")
    return True

def handle_complete_tournament(vk, user_id, send_message):
    """Обработка кнопки 'Завершить турнир' (только админ)"""
    logger.info(f"🔹 Админ завершает турнир")
    
    active_tournaments = get_active_tournaments()
    
    if not active_tournaments:
        send_message(vk, user_id, "❌ Нет активных турниров для завершения.")
        return
    
    tournaments_text = "🏆 Активные турниры (введите номер для завершения):\n\n"
    waiting_for_tournament_reg[user_id] = active_tournaments
    for i, t in enumerate(active_tournaments, 1):
        tournaments_text += f"{i}. {t['name']} ({t['date']})\n"
    
    send_message(vk, user_id, tournaments_text)

def handle_tournament_complete_selection(vk, user_id, text, send_message):
    """Обработка выбора турнира для завершения"""
    if user_id not in waiting_for_tournament_reg:
        return False
    
    try:
        num = int(text)
        tournaments = waiting_for_tournament_reg[user_id]
        
        if 1 <= num <= len(tournaments):
            tournament = tournaments[num - 1]
            complete_tournament(tournament['id'])
            send_message(vk, user_id, f"✅ Турнир '{tournament['name']}' завершён!")
        else:
            send_message(vk, user_id, "❌ Неверный номер.")
        
        del waiting_for_tournament_reg[user_id]
        return True
        
    except ValueError:
        send_message(vk, user_id, "❌ Введите номер турнира цифрой.")
        return True

def handle_list_tournaments(vk, user_id, send_message):
    """Обработка кнопки 'Список турниров'"""
    tournaments = get_all_tournaments()
    
    if not tournaments:
        send_message(vk, user_id, "📋 Нет турниров.")
        return
    
    text = "📋 ВСЕ ТУРНИРЫ:\n\n"
    for t in tournaments:
        status = "✅ Активен" if t['status'] == 'active' else "🏁 Завершён"
        text += f"🏆 {t['name']}\n   📅 {t['date']}\n   {status}\n\n"
    
    send_message(vk, user_id, text)

def handle_back(vk, user_id, send_message, get_main_keyboard):
    """Обработка кнопки 'Назад'"""
    send_message(vk, user_id, "Главное меню:", get_main_keyboard())

# Функции для проверки состояний
def is_waiting_for_tournament_name(user_id):
    return user_id in waiting_for_tournament_name

def is_waiting_for_tournament_date(user_id):
    return user_id in waiting_for_tournament_date

def is_waiting_for_tournament_reg(user_id):
    return user_id in waiting_for_tournament_reg