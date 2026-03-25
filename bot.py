import vk_api
import os
import logging
from dotenv import load_dotenv
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

load_dotenv()

TOKEN = os.getenv("VK_TOKEN")
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ========== КЛАВИАТУРЫ ==========
def get_main_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("💰 Стать спонсором клуба", color=VkKeyboardColor.PRIMARY)
    logger.debug("Создана главная клавиатура")
    return keyboard

def get_sponsor_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("✅ Подтвердить оплату", color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button("❌ Отписаться", color=VkKeyboardColor.NEGATIVE)
    logger.debug("Создана клавиатура спонсора")
    return keyboard

# ========== ФУНКЦИЯ ОТПРАВКИ ==========
def send_keyboard(user_id, message, keyboard):
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
        
        # === ОБРАБОТКА КОМАНД ===
        
        # Команда /start
        if text == "/start" or text.lower() == "начать":
            logger.info(f"🔹 Обработка /start для {user_id}")
            send_keyboard(user_id, "👋 Добро пожаловать!\n\n💰 Нажмите кнопку:", get_main_keyboard())
        
        # Кнопка "Стать спонсором"
        elif text == "💰 Стать спонсором клуба":
            logger.info(f"🔹 Обработка 'Стать спонсором' для {user_id}")
            send_keyboard(user_id, "✅ Вы зарегистрированы!\n\nВыберите действие:", get_sponsor_keyboard())
        
        # Кнопка "Подтвердить оплату"
        elif text == "✅ Подтвердить оплату":
            logger.info(f"🔹 Обработка 'Подтвердить оплату' для {user_id}")
            vk.messages.send(
                user_id=user_id,
                message="📸 Отправьте фото подтверждения оплаты:",
                random_id=0
            )
        
        # Кнопка "Отписаться"
        elif text == "❌ Отписаться":
            logger.info(f"🔹 Обработка 'Отписаться' для {user_id}")
            send_keyboard(user_id, "❌ Вы отписались.\n\nЧтобы вернуться, нажмите /start", get_main_keyboard())
        
        # Неизвестная команда
        else:
            logger.info(f"🔹 Неизвестная команда от {user_id}: '{text}'")
            vk.messages.send(
                user_id=user_id,
                message="❓ Неизвестная команда.\n\nНажмите /start для начала работы.",
                random_id=0
            )