import vk_api
import os
import logging
from dotenv import load_dotenv
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

load_dotenv()

TOKEN = os.getenv("VK_TOKEN")
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем клавиатуры
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

vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkLongPoll(vk_session)

logger.info("🚀 Бот запущен (упрощенная версия)")

for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        user_id = event.user_id
        text = event.text if event.text else ""
        
        logger.info(f"📨 Получено: '{text}' от {user_id}")
        
        # Простая логика
        if text == "/start" or text == "Начать" or text == "начать":
            # Отправляем главную клавиатуру
            vk.messages.send(
                user_id=user_id,
                message="Добро пожаловать!\n\n💰 Нажмите кнопку:",
                keyboard=get_main_keyboard().get_keyboard(),
                random_id=0
            )
            logger.info(f"📤 Отправлена главная клавиатура для {user_id}")
        
        elif text == "💰 Стать спонсором клуба":
            vk.messages.send(
                user_id=user_id,
                message="Вы зарегистрированы как спонсор!\n\nТеперь доступны кнопки:",
                keyboard=get_sponsor_keyboard().get_keyboard(),
                random_id=0
            )
            logger.info(f"📤 Отправлена клавиатура спонсора для {user_id}")
        
        elif text == "✅ Подтвердить оплату":
            vk.messages.send(
                user_id=user_id,
                message="Отправьте фото подтверждения оплаты:",
                random_id=0
            )
            logger.info(f"📤 Запрошено фото от {user_id}")
        
        elif text == "❌ Отписаться":
            vk.messages.send(
                user_id=user_id,
                message="Вы отписались от спонсорства.\n\nЧтобы вернуться, нажмите /start",
                keyboard=get_main_keyboard().get_keyboard(),
                random_id=0
            )
            logger.info(f"📤 Отписка для {user_id}")
        
        else:
            vk.messages.send(
                user_id=user_id,
                message="Используйте кнопки для управления.\n\nНажмите /start для начала.",
                random_id=0
            )