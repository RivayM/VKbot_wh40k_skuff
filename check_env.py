import os
from dotenv import load_dotenv

# Загружаем .env файл
load_dotenv()

# Получаем переменные
token = os.getenv("VK_TOKEN")
admin_id = os.getenv("ADMIN_ID")

# Проверяем и выводим
print("=" * 50)
print("Проверка .env файла")
print("=" * 50)

if token:
    print(f"✅ VK_TOKEN найден: {token[:20]}... (первые 20 символов)")
else:
    print("❌ VK_TOKEN НЕ НАЙДЕН в .env файле")

if admin_id:
    print(f"✅ ADMIN_ID найден: {admin_id}")
else:
    print("❌ ADMIN_ID НЕ НАЙДЕН в .env файле")

# Показываем содержимое .env файла
print("\n" + "=" * 50)
print("Содержимое .env файла:")
print("=" * 50)
try:
    with open(".env", "r", encoding="utf-8") as f:
        content = f.read()
        # Скрываем полный токен для безопасности
        lines = content.split("\n")
        for line in lines:
            if line.startswith("VK_TOKEN"):
                print("VK_TOKEN=***скрыто***")
            elif line.startswith("ADMIN_ID"):
                print(line)
            elif line.strip():
                print(line)
except FileNotFoundError:
    print("❌ Файл .env не существует!")