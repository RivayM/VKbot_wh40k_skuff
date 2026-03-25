from vk_api.keyboard import VkKeyboard, VkKeyboardColor

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

def get_confirmation_keyboard(action, user_id):
    keyboard = VkKeyboard(inline=True)
    keyboard.add_button("✅ Да", color=VkKeyboardColor.POSITIVE, payload={"action": f"confirm_{action}", "user_id": user_id})
    keyboard.add_button("❌ Нет", color=VkKeyboardColor.NEGATIVE, payload={"action": "cancel"})
    return keyboard

def get_admin_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("📊 Список спонсоров", color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button("📸 Не прислали фото", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("✅ Прислали фото", color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button("📅 Назначить дату оплаты", color=VkKeyboardColor.SECONDARY)
    return keyboard