import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("VK_TOKEN")
admin_id = os.getenv("ADMIN_ID")

print("=" * 50)
print("Проверка .env файла")
print("=" * 50)

if token:
    print(f"✅ VK_TOKEN найден: {token[:20]}...")
else:
    print("❌ VK_TOKEN НЕ НАЙДЕН")

if admin_id:
    print(f"✅ ADMIN_ID найден: {admin_id}")
else:
    print("❌ ADMIN_ID НЕ НАЙДЕН")

try:
    with open(".env", "r", encoding="utf-8") as f:
        print("\nСодержимое .env:")
        for line in f:
            if line.startswith("VK_TOKEN"):
                print("VK_TOKEN=***скрыто***")
            elif line.strip():
                print(line.strip())
except FileNotFoundError:
    print("\n❌ Файл .env не существует!")
