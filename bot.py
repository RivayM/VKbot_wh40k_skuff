import vk_api
import os
import logging
from dotenv import load_dotenv
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor


# Импорт базы данных
from database import init_db, add_sponsor, get_sponsor, remove_sponsor

load_dotenv()

TOKEN = os.getenv("VK_TOKEN")
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Инициализация базы данных
init_db()
logger.info("✅ База данных подключена")

# ========== КЛАВИАТУРЫ ==========
def get_main_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("💰 Стать спонсором клуба", color=VkKeyboardColor.PRIMARY)
    return keyboard

def get_sponsor_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("✅ Подтвердить оплату", color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button("❌ Отписаться", color=VkKeyboardColor.NEGATIVE)
    return keyboard

# ========== ФУНКЦИЯ ОТПРАВКИ ==========
def send_keyboard(vk, user_id, message, keyboard):
    """Отправка сообщения с клавиатурой"""
    try:
        vk.messages.send(
            user_id=user_id,
            message=message,
            keyboard=keyboard.get_keyboard(),
            random_id=0
        )
        logger.info(f"✅ Клавиатура отправлена пользователю {user_id}")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка отправки клавиатуры: {e}")
        return False

# ========== ХРАНИЛИЩЕ ДЛЯ ОЖИДАНИЯ ВВОДА ==========
waiting_for_name = {}

# ========== ОСНОВНОЙ КОД ==========
vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkLongPoll(vk_session)

logger.info("=" * 50)
logger.info("🚀 БОТ ЗАПУЩЕН")
logger.info(f"📱 Админы: {ADMIN_IDS}")
logger.info("=" * 50)

for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        user_id = event.user_id
        text = event.text.strip() if event.text else ""
        
        logger.info(f"📨 Сообщение от {user_id}: '{text}'")
        
        # === ОБРАБОТКА ОЖИДАНИЯ ВВОДА ИМЕНИ ===
        if user_id in waiting_for_name:
            name = text
            if len(name) > 50:
                vk.messages.send(
                    user_id=user_id,
                    message="❌ Имя слишком длинное. Пожалуйста, введите имя короче (до 50 символов):",
                    random_id=0
                )
                continue
            
            # Сохраняем спонсора
            add_sponsor(user_id, name)
            del waiting_for_name[user_id]
            
            vk.messages.send(
                user_id=user_id,
                message=f"✅ Отлично, {name}! Вы зарегистрированы как спонсор!\n\nТеперь доступны кнопки:",
                keyboard=get_sponsor_keyboard().get_keyboard(),
                random_id=0
            )
            continue
        
        # === ОБРАБОТКА КОМАНД ===
        
        # Команда /start
        if text == "/start" or text.lower() == "начать":
            logger.info(f"🔹 Обработка /start для {user_id}")
            sponsor = get_sponsor(user_id)
            if sponsor and sponsor['status'] == 'active':
                send_keyboard(vk, user_id, "✅ Вы уже являетесь спонсором!\n\nВыберите действие:", get_sponsor_keyboard())
            else:
                send_keyboard(vk, user_id, "👋 Добро пожаловать!\n\n💰 Нажмите кнопку, чтобы стать спонсором:", get_main_keyboard())
        
        # Кнопка "Стать спонсором"
        elif text == "💰 Стать спонсором клуба":
            logger.info(f"🔹 Обработка 'Стать спонсором' для {user_id}")
            sponsor = get_sponsor(user_id)
            if sponsor and sponsor['status'] == 'active':
                vk.messages.send(
                    user_id=user_id,
                    message="❌ Вы уже являетесь спонсором!",
                    keyboard=get_sponsor_keyboard().get_keyboard(),
                    random_id=0
                )
            else:
                waiting_for_name[user_id] = True
                vk.messages.send(
                    user_id=user_id,
                    message="📝 Введите ваше имя (как вы хотите, чтобы вас называли):",
                    random_id=0
                )
        
        # Кнопка "Подтвердить оплату"
        elif text == "✅ Подтвердить оплату":
            logger.info(f"🔹 Обработка 'Подтвердить оплату' для {user_id}")
            sponsor = get_sponsor(user_id)
            if not sponsor or sponsor['status'] != 'active':
                vk.messages.send(
                    user_id=user_id,
                    message="❌ Вы не зарегистрированы как спонсор. Нажмите 'Стать спонсором клуба'",
                    random_id=0
                )
            else:
                vk.messages.send(
                    user_id=user_id,
                    message="📸 Отправьте фото подтверждения оплаты:",
                    random_id=0
                )
        
        # Кнопка "Отписаться"
        elif text == "❌ Отписаться":
            logger.info(f"🔹 Обработка 'Отписаться' для {user_id}")
            sponsor = get_sponsor(user_id)
            if sponsor and sponsor['status'] == 'active':
                remove_sponsor(user_id)
                vk.messages.send(
                    user_id=user_id,
                    message="❌ Вы отписались от спонсорства.\n\nЧтобы вернуться, нажмите /start",
                    keyboard=get_main_keyboard().get_keyboard(),
                    random_id=0
                )
            else:
                vk.messages.send(
                    user_id=user_id,
                    message="❌ Вы не являетесь спонсором.\n\nНажмите /start для начала.",
                    random_id=0
                )
        
        # Неизвестная команда
        else:
            vk.messages.send(
                user_id=user_id,
                message="❓ Неизвестная команда.\n\nНажмите /start для начала работы.",
                random_id=0
            )