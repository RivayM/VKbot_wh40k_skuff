print("START")
import sys
sys.stdout.flush()

try:
    print("1. Импорт vk_api...")
    import vk_api
    print("✅ vk_api импортирован")
    
    print("2. Импорт dotenv...")
    from dotenv import load_dotenv
    print("✅ dotenv импортирован")
    
    print("3. Загрузка .env...")
    load_dotenv()
    print("✅ .env загружен")
    
    print("4. Чтение токена...")
    import os
    TOKEN = os.getenv("VK_TOKEN")
    if TOKEN:
        print(f"✅ Токен найден: {TOKEN[:20]}...")
    else:
        print("❌ Токен НЕ НАЙДЕН!")
    
    ADMIN_IDS = os.getenv("ADMIN_IDS")
    print(f"ADMIN_IDS: {ADMIN_IDS}")
    
    print("END - Все проверки пройдены!")
    
except Exception as e:
    print(f"❌ ОШИБКА: {e}")
    import traceback
    traceback.print_exc()