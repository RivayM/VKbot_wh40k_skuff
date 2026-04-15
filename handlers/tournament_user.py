# handlers/tournament_user.py
import logging
from database import tournament_db as db
from keyboards import get_tournament_user_keyboard, get_tournament_actions_keyboard
from utils.helpers import send_message, extract_photo_url

logger = logging.getLogger(__name__)

# Хранилища состояний
waiting_for_tournament_choice = {}
selected_tournament = {}
waiting_for_registration_name = {}
waiting_for_registration_army = {}
waiting_for_registration_roster = {}
waiting_for_payment_photo = {}
waiting_for_match_result = {}
waiting_for_new_tournament_name = {}
waiting_for_new_tournament_date = {}
waiting_for_new_tournament_max_players = {}
waiting_for_tour_announcement = {}  # user_id -> tournament_id
waiting_for_edit_choice = {}   # user_id -> registration_id
waiting_for_edit_army = {}     # user_id -> registration_id
waiting_for_edit_roster = {}   # user_id -> registration_id
# ------------------------------------------------------------
# Общие функции
# ------------------------------------------------------------
def handle_tournament_user_menu(vk, user_id, send_message_func):
    send_message_func(vk, user_id, "🎮 Турнирное меню:", get_tournament_user_keyboard())

def handle_list_tournaments_user(vk, user_id, send_message_func, is_admin=False):
    tournaments = db.get_all_tournaments()
    active = [t for t in tournaments if t['status'] in ('pending', 'active')]
    if not active:
        send_message_func(vk, user_id, "❌ Нет активных турниров.")
        return
    text = "📋 Выберите турнир (введите номер):\n\n"
    for idx, t in enumerate(active, 1):
        text += f"{idx}. {t['name']} ({t['date']})\n"
    waiting_for_tournament_choice[user_id] = ('list', active)
    send_message_func(vk, user_id, text)

def show_tournament_actions(vk, user_id, tournament, send_message_func, is_admin=False):
    # Проверяем, существует ли турнир в базе
    check_tournament = db.get_tournament(tournament['id'])
    if not check_tournament:
        send_message_func(vk, user_id, "❌ Турнир был удалён. Возврат в главное меню.")
        if user_id in selected_tournament:
            del selected_tournament[user_id]
        handle_tournament_user_menu(vk, user_id, send_message_func)
        return
    reg = db.get_registration_by_user(tournament['id'], user_id)
    if reg:
        msg = f"✅ Вы зарегистрированы на турнир '{tournament['name']}'\n👤 Имя: {reg['player_name']}\n⚔️ Армия: {reg['army_name'] if reg['army_name'] else 'Не указана'}"
        send_message_func(vk, user_id, msg, get_tournament_actions_keyboard(registered=True, is_admin=is_admin))
    else:
        msg = f"📋 Турнир: {tournament['name']}\n📅 Дата: {tournament['date']}\n\nВыберите действие:"
        send_message_func(vk, user_id, msg, get_tournament_actions_keyboard(registered=False, is_admin=is_admin))

# ------------------------------------------------------------
# Обработка выбора турнира
# ------------------------------------------------------------
def handle_tournament_selection(vk, user_id, text, send_message_func, is_admin=False):
    if user_id not in waiting_for_tournament_choice:
        return False
    step, data = waiting_for_tournament_choice[user_id]
    if step == 'list':
        try:
            idx = int(text)
            if 1 <= idx <= len(data):
                tournament = data[idx-1]
                del waiting_for_tournament_choice[user_id]
                selected_tournament[user_id] = tournament
                show_tournament_actions(vk, user_id, tournament, send_message_func, is_admin)
                return True
            else:
                send_message_func(vk, user_id, "❌ Неверный номер.")
                return True
        except ValueError:
            send_message_func(vk, user_id, "❌ Введите номер цифрой.")
            return True
    elif step == 'delete':
        try:
            idx = int(text)
            if 1 <= idx <= len(data):
                tournament = data[idx-1]
                del waiting_for_tournament_choice[user_id]
                waiting_for_tournament_choice[user_id] = ('confirm_delete', tournament)
                send_message_func(vk, user_id, f"Вы уверены, что хотите удалить турнир '{tournament['name']}'? (да/нет)")
                return True
            else:
                send_message_func(vk, user_id, "❌ Неверный номер.")
                return True
        except ValueError:
            send_message_func(vk, user_id, "❌ Введите номер цифрой.")
            return True
    elif step == 'confirm_delete':
        tournament = data
        if text.lower() in ['да', 'yes', 'y']:
            db.delete_tournament(tournament['id'])
            send_message_func(vk, user_id, f"✅ Турнир '{tournament['name']}' удалён!")
            from keyboards import get_tournament_user_keyboard
            send_message_func(vk, user_id, "⚙️ Управление турнирами:", get_tournament_user_keyboard(is_admin=True))
        else:
            send_message_func(vk, user_id, "❌ Удаление отменено.")
        del waiting_for_tournament_choice[user_id]
        return True
    return False

# ------------------------------------------------------------
# Работа с турниром
# ------------------------------------------------------------
def handle_tournament_start(vk, user_id, send_message_func):
    if user_id not in selected_tournament:
        send_message_func(vk, user_id, "❌ Сначала выберите турнир.")
        return
    tournament = selected_tournament[user_id]
    registrations = db.get_registrations(tournament['id'])
    if not registrations:
        send_message_func(vk, user_id, "❌ Нет зарегистрированных игроков.")
        return
    msg = f"🏆 ТУРНИР «{tournament['name']}» НАЧАЛСЯ!\n\nОжидайте пары для первого тура."
    for reg in registrations:
        try:
            send_message_func(vk, reg['user_id'], msg)
        except:
            pass
    send_message_func(vk, user_id, f"✅ Сообщение о начале турнира отправлено {len(registrations)} игрокам.")

def handle_tour_announcement(vk, user_id, send_message_func):
    """Админ начинает рассылку сообщения о туре"""
    if user_id not in selected_tournament:
        send_message_func(vk, user_id, "❌ Сначала выберите турнир.")
        return
    tournament = selected_tournament[user_id]
    waiting_for_tour_announcement[user_id] = tournament['id']
    send_message_func(vk, user_id, "📢 Введите номер тура и текст сообщения (например: '1\\nНачинаем первый тур!'):")

def handle_tour_announcement_input(vk, user_id, text, send_message_func):
    if user_id not in waiting_for_tour_announcement:
        return False
    tournament_id = waiting_for_tour_announcement.pop(user_id)
    lines = text.strip().split('\n', 1)
    if len(lines) < 2:
        send_message_func(vk, user_id, "❌ Введите номер тура и текст в двух строках.")
        return True
    try:
        round_num = int(lines[0].strip())
        message = lines[1].strip()
    except:
        send_message_func(vk, user_id, "❌ Неверный формат. Первая строка – номер тура (число).")
        return True
    
    # Получаем всех зарегистрированных игроков
    registrations = db.get_registrations(tournament_id)
    if not registrations:
        send_message_func(vk, user_id, "❌ Нет зарегистрированных игроков.")
        return True
    
    for reg in registrations:
        try:
            send_message_func(vk, reg['user_id'], 
                f"📢 Турнир: {db.get_tournament(tournament_id)['name']}\n"
                f"🔢 Тур {round_num}\n\n{message}")
        except:
            pass
    send_message_func(vk, user_id, f"✅ Сообщение о {round_num} туре отправлено {len(registrations)} игрокам.")
    return True

def handle_finish_tournament(vk, user_id, send_message_func):
    """Админ завершает турнир и рассылает результаты"""
    if user_id not in selected_tournament:
        send_message_func(vk, user_id, "❌ Сначала выберите турнир.")
        return
    tournament = selected_tournament[user_id]
    leaderboard = db.get_leaderboard(tournament['id'])
    if not leaderboard:
        send_message_func(vk, user_id, "❌ Нет данных для завершения.")
        return
    
    # Формируем итоговую таблицу
    result_text = f"🏆 ТУРНИР ЗАВЕРШЁН: {tournament['name']}\n\n"
    for idx, (_, _, name, to, vp) in enumerate(leaderboard, 1):
        result_text += f"{idx}. {name} — ТО: {to}, ВП: {vp}\n"
    
    # Рассылаем всем участникам
    registrations = db.get_registrations(tournament['id'])
    for reg in registrations:
        try:
            send_message_func(vk, reg['user_id'], result_text)
        except:
            pass
    
    # Меняем статус турнира на completed
    db.update_tournament(tournament['id'], status='completed')
    send_message_func(vk, user_id, "✅ Турнир завершён, результаты отправлены игрокам.")
    
    # Сбрасываем выбранный турнир
    if user_id in selected_tournament:
        del selected_tournament[user_id]

# ------------------------------------------------------------
# Регистрация игрока
# ------------------------------------------------------------
def handle_register_user(vk, user_id, send_message_func):
    if user_id not in selected_tournament:
        send_message_func(vk, user_id, "❌ Сначала выберите турнир через 'Выбрать турнир'.")
        return
    tournament = selected_tournament[user_id]
    if db.is_registered(tournament['id'], user_id):
        send_message_func(vk, user_id, "❌ Вы уже зарегистрированы.")
        return
    player = db.get_or_create_player(user_id)
    waiting_for_registration_name[user_id] = tournament['id']
    send_message_func(vk, user_id, f"📝 Введите ваше имя (или оставьте '{player['default_name']}'):")

def handle_registration_name(vk, user_id, text, send_message_func):
    if user_id not in waiting_for_registration_name:
        return False
    tournament_id = waiting_for_registration_name.pop(user_id)
    player_name = text.strip() if text.strip() else db.get_or_create_player(user_id)['default_name']
    waiting_for_registration_army[user_id] = (tournament_id, player_name)
    armies = db.get_player_armies(user_id)
    if armies:
        text_armies = "Выберите армию (введите номер):\n\n"
        for idx, a in enumerate(armies, 1):
            text_armies += f"{idx}. {a['army_name']} (В:{a['wins']} Н:{a['draws']} П:{a['losses']})\n"
        text_armies += f"{len(armies)+1}. Новая армия"
        waiting_for_registration_army[user_id] = (tournament_id, player_name, armies)
        send_message_func(vk, user_id, text_armies)
    else:
        waiting_for_registration_army[user_id] = (tournament_id, player_name, None)
        send_message_func(vk, user_id, "Введите название вашей армии:")
    return True

def handle_registration_army(vk, user_id, text, send_message_func, admin_ids):
    if user_id not in waiting_for_registration_army:
        return False
    data = waiting_for_registration_army[user_id]
    if len(data) == 2:
        tournament_id, player_name = data
        armies = None
    else:
        tournament_id, player_name, armies = data

    if armies is not None and isinstance(armies, list):
        try:
            choice = int(text)
            if 1 <= choice <= len(armies):
                army_id = armies[choice-1]['id']
                # Регистрируем с пустым ростера
                db.register_for_tournament(tournament_id, user_id, player_name, army_id, '')
                send_message_func(vk, user_id, "✅ Вы успешно зарегистрированы!")
                # Уведомляем админов
                tournament = db.get_tournament(tournament_id)
                for admin_id in admin_ids:
                    try:
                        send_message_func(vk, admin_id, 
                            f"📢 **Новая регистрация на турнир**\n"
                            f"🏆 Турнир: {tournament['name']}\n"
                            f"👤 Игрок: {player_name}\n"
                            f"⚔️ Армия: {armies[choice-1]['army_name']}")
                    except:
                        pass
                if tournament:
                    show_tournament_actions(vk, user_id, tournament, send_message_func)
                else:
                    handle_tournament_user_menu(vk, user_id, send_message_func)
                return True
            elif choice == len(armies)+1:
                waiting_for_registration_army[user_id] = (tournament_id, player_name, 'new')
                send_message_func(vk, user_id, "Введите название новой армии:")
                return True
            else:
                send_message_func(vk, user_id, "❌ Неверный номер.")
                return True
        except ValueError:
            pass

    # Новая армия
    new_army_name = text.strip()
    if not new_army_name:
        send_message_func(vk, user_id, "❌ Название армии не может быть пустым.")
        return True
    army_id = db.add_army(user_id, new_army_name)
    db.register_for_tournament(tournament_id, user_id, player_name, army_id, '')
    send_message_func(vk, user_id, "✅ Вы успешно зарегистрированы!")
    tournament = db.get_tournament(tournament_id)
    for admin_id in admin_ids:
        try:
            send_message_func(vk, admin_id, 
                f"📢 **Новая регистрация на турнир**\n"
                f"🏆 Турнир: {tournament['name']}\n"
                f"👤 Игрок: {player_name}\n"
                f"⚔️ Армия: {new_army_name}")
        except:
            pass
    if tournament:
        show_tournament_actions(vk, user_id, tournament, send_message_func)
    else:
        handle_tournament_user_menu(vk, user_id, send_message_func)
    return True

def handle_registration_roster(vk, user_id, text, send_message_func):
    if user_id not in waiting_for_registration_roster:
        return False
    tournament_id, player_name, army_id = waiting_for_registration_roster.pop(user_id)
    roster_text = text.strip()
    if not roster_text:
        roster_text = ''
    try:
        db.register_for_tournament(tournament_id, user_id, player_name, army_id, roster_text)
        send_message_func(vk, user_id, "✅ Вы успешно зарегистрированы!")
        tournament = db.get_tournament(tournament_id)
        if tournament:
            show_tournament_actions(vk, user_id, tournament, send_message_func)
        else:
            handle_tournament_user_menu(vk, user_id, send_message_func)
    except Exception as e:
        logger.error(f"Ошибка регистрации: {e}")
        send_message_func(vk, user_id, f"❌ Ошибка регистрации. Попробуйте позже.\nТекст ошибки: {e}")
        # Возвращаем пользователя в меню выбора действий (чтобы он мог попробовать снова)
        tournament = db.get_tournament(tournament_id)
        if tournament:
            show_tournament_actions(vk, user_id, tournament, send_message_func)
        else:
            handle_tournament_user_menu(vk, user_id, send_message_func)
    return True

# ------------------------------------------------------------
# Оплата
# ------------------------------------------------------------
def handle_payment(vk, user_id, send_message_func):
    if user_id not in selected_tournament:
        send_message_func(vk, user_id, "❌ Сначала выберите турнир.")
        return
    tournament = selected_tournament[user_id]
    waiting_for_payment_photo[user_id] = tournament['id']
    send_message_func(vk, user_id, "💳 Пришлите фото подтверждения оплаты.")

def handle_payment_photo(vk, user_id, attachments, send_message_func, admin_ids):
    if user_id not in waiting_for_payment_photo:
        return False
    tournament_id = waiting_for_payment_photo.pop(user_id)
    photo_url = extract_photo_url(attachments)
    if not photo_url:
        send_message_func(vk, user_id, "❌ Не удалось получить фото.")
        return True
    db.add_payment(tournament_id, user_id, photo_url)
    tournament = db.get_tournament(tournament_id)
    player = db.get_or_create_player(user_id)
    for admin_id in admin_ids:
        try:
            send_message_func(vk, admin_id, f"💸 **Новая оплата турнира**\nТурнир: {tournament['name']}\nИгрок: {player['default_name']} (id{user_id})\nФото: {photo_url}")
        except Exception as e:
            logger.error(f"Ошибка уведомления админа {admin_id}: {e}")
    send_message_func(vk, user_id, "✅ Фото отправлено администратору.")
    return True

# ------------------------------------------------------------
# Начало матча и ввод результата
# ------------------------------------------------------------
def handle_start_match(vk, user_id, send_message_func):
    if user_id not in selected_tournament:
        send_message_func(vk, user_id, "❌ Сначала выберите турнир.")
        return
    tournament = selected_tournament[user_id]
    reg = db.get_registration_by_user(tournament['id'], user_id)
    if not reg:
        send_message_func(vk, user_id, "❌ Вы не зарегистрированы.")
        return
    matches = db.get_matches_by_round(tournament['id'], 1)
    for match in matches:
        if (match['registration1_id'] == reg['id'] or match['registration2_id'] == reg['id']) and match['status'] == 'pending':
            waiting_for_match_result[user_id] = (match['id'], match['registration1_id'] == reg['id'])
            opponent = match['player2_name'] if match['player2_name'] else 'БОТА'
            send_message_func(vk, user_id, f"🎮 Ваш матч против {opponent}\nВведите результат в формате 'X-Y' (ваши-соперника)\nДля бота: просто число")
            return
    send_message_func(vk, user_id, "⏳ Ваша пара ещё не создана.")

def handle_match_result(vk, user_id, text, send_message_func):
    if user_id not in waiting_for_match_result:
        return False
    match_id, is_first = waiting_for_match_result[user_id]
    match = db.get_match(match_id)
    if not match or match['status'] != 'pending':
        send_message_func(vk, user_id, "❌ Матч уже завершён.")
        del waiting_for_match_result[user_id]
        return True
    text = text.strip()
    if '-' in text:
        parts = text.split('-')
        if len(parts) == 2:
            try:
                vp1 = int(parts[0].strip())
                vp2 = int(parts[1].strip())
                if is_first:
                    db.update_match_result(match_id, vp1, vp2)
                else:
                    db.update_match_result(match_id, vp2, vp1)
                send_message_func(vk, user_id, f"✅ Результат принят: {vp1} - {vp2}")
                del waiting_for_match_result[user_id]
                return True
            except ValueError:
                send_message_func(vk, user_id, "❌ Неверный формат.")
                return True
    else:
        if match['registration2_id'] is None:
            try:
                vp = int(text)
                if is_first:
                    db.update_match_result(match_id, vp, 0)
                else:
                    db.update_match_result(match_id, 0, vp)
                send_message_func(vk, user_id, f"✅ Результат принят: {vp} - 0")
                del waiting_for_match_result[user_id]
                return True
            except ValueError:
                send_message_func(vk, user_id, "❌ Введите число.")
                return True
        else:
            send_message_func(vk, user_id, "❌ Для игры с человеком используйте 'X-Y'.")
            return True

def handle_show_players_list(vk, user_id, send_message_func):
    if user_id not in selected_tournament:
        send_message_func(vk, user_id, "❌ Сначала выберите турнир.")
        return
    tournament = selected_tournament[user_id]
    leaderboard = db.get_leaderboard(tournament['id'])
    if not leaderboard:
        send_message_func(vk, user_id, "Нет данных об игроках.")
        return
    text = "🏆 ТАБЛИЦА ИГРОКОВ (по очкам):\n\n"
    for idx, (_, _, name, to, vp) in enumerate(leaderboard, 1):
        text += f"{idx}. {name} — ТО: {to}, ВП: {vp}\n"
    send_message_func(vk, user_id, text)

# ------------------------------------------------------------
# Админские функции
# ------------------------------------------------------------
def handle_admin_create_tournament(vk, user_id, send_message_func):
    waiting_for_new_tournament_name[user_id] = True
    send_message_func(vk, user_id, "📝 Введите название турнира:")

def handle_new_tournament_name(vk, user_id, text, send_message_func):
    if user_id not in waiting_for_new_tournament_name:
        return False
    tournament_name = text.strip()
    del waiting_for_new_tournament_name[user_id]
    waiting_for_new_tournament_date[user_id] = tournament_name   # сохраняем название, а не True
    send_message_func(vk, user_id, "📅 Введите дату турнира (например: 25.04.2026):")
    return True

def handle_new_tournament_date(vk, user_id, text, send_message_func):
    if user_id not in waiting_for_new_tournament_date:
        return False
    name = waiting_for_new_tournament_date.pop(user_id)
    waiting_for_new_tournament_max_players[user_id] = (name, text.strip())
    send_message_func(vk, user_id, "👥 Введите максимальное количество участников (0 - без ограничений):")
    return True

def handle_new_tournament_max_players(vk, user_id, text, send_message_func):
    if user_id not in waiting_for_new_tournament_max_players:
        return False
    name, date = waiting_for_new_tournament_max_players.pop(user_id)
    try:
        max_players = int(text) if text.isdigit() and int(text) > 0 else None
    except:
        max_players = None
    db.create_tournament(name, date, max_players)
    from keyboards import get_tournament_user_keyboard
    send_message_func(vk, user_id, f"✅ Турнир '{name}' создан!\n\n⚙️ Управление турнирами:",
                      get_tournament_user_keyboard(is_admin=True))
    return True

def handle_admin_delete_tournament(vk, user_id, send_message_func):
    tournaments = db.get_all_tournaments()
    active = [t for t in tournaments if t['status'] in ('pending', 'active')]
    if not active:
        send_message_func(vk, user_id, "❌ Нет активных турниров для удаления.")
        return
    text = "🗑️ Выберите турнир для удаления (введите номер):\n\n"
    for idx, t in enumerate(active, 1):
        text += f"{idx}. {t['name']} ({t['date']})\n"
    waiting_for_tournament_choice[user_id] = ('delete', active)
    send_message_func(vk, user_id, text)
    
    # ------------------------------------------------------------
    # Показывает меню выбора: изменить армию или ростер
    # ------------------------------------------------------------
def handle_edit_my_data(vk, user_id, send_message_func):
    """Удаляет старую регистрацию и запускает процесс регистрации заново"""
    if user_id not in selected_tournament:
        send_message_func(vk, user_id, "❌ Сначала выберите турнир.")
        return
    tournament = selected_tournament[user_id]
    reg = db.get_registration_by_user(tournament['id'], user_id)
    if not reg:
        send_message_func(vk, user_id, "❌ Вы не зарегистрированы на этот турнир.")
        return
    # Удаляем старую регистрацию
    db.delete_registration(reg['id'])
    # Запускаем процесс регистрации заново
    handle_register_user(vk, user_id, send_message_func)