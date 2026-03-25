import os

TOKEN = os.getenv("VK_TOKEN")
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
PAYMENT_DEADLINE_DAY = int(os.getenv("PAYMENT_DEADLINE_DAY", "25"))