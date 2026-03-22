import vk_api
import os
from dotenv import load_dotenv
from vk_api.longpoll import VkLongPoll, VkEventType

load_dotenv()

TOKEN = os.getenv("VK_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# Подключаемся к VK
vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkLongPoll(vk_session)

print("=" * 50)
print("🚀 Бот запущен!")
print(f"✅ Токен: {TOKEN[:20]}...")
print(f"✅ ID админа: {ADMIN_ID}")
print("💡 Напишите сообщение в сообщество")
print("=" * 50)

# Слушаем сообщения
for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        user_id = event.user_id
        text = event.text
        
        print(f"\n📨 Сообщение от {user_id}: {text}")
        
        # Пропускаем сообщения от админа
        # if user_id == ADMIN_ID:
        #     print("⏭️ Это админ, не отвечаем")
         #    continue
        
        # Отправляем ответ
        vk.messages.send(
            user_id=user_id,
            message=f"✅ Ваше сообщение получено: {text}",
            random_id=0
        )
        print(f"✅ Ответ отправлен пользователю {user_id}")