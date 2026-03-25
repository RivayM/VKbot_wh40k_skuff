import vk_api
from database.db import get_sponsor, save_payment_photo, set_photo_sent
from keyboards.keyboards import get_confirmation_keyboard, get_sponsor_keyboard

# Хранилище ожидания фото
waiting_for_photo = {}

def handle_payment_request(vk, event):
    """Запрос на подтверждение оплаты"""
    user_id = event.user_id
    
    sponsor = get_sponsor(user_id)
    if not sponsor or sponsor['status'] != 'active':
        vk.messages.send(
            user_id=user_id,
            message="Вы не зарегистрированы как спонсор. Сначала нажмите 'Стать спонсором клуба'.",
            random_id=0
        )
        return
    
    # Запрашиваем фото
    waiting_for_photo[user_id] = True
    vk.messages.send(
        user_id=user_id,
        message="📸 Пожалуйста, отправьте фото подтверждения оплаты:",
        random_id=0
    )

def handle_photo_input(bot, vk, event, ADMIN_IDS, attachments):
    """Обработка полученного фото"""
    user_id = event.user_id
    
    if user_id not in waiting_for_photo:
        return False
    
    # Получаем фото
    photo_url = None
    for attachment in attachments:
        if attachment.get('type') == 'photo':
            photo = attachment.get('photo', {})
            # Берем самую большую версию фото
            sizes = photo.get('sizes', [])
            if sizes:
                photo_url = sizes[-1].get('url')
            break
    
    if not photo_url:
        vk.messages.send(
            user_id=user_id,
            message="❌ Не удалось получить фото. Пожалуйста, отправьте фото еще раз.",
            random_id=0
        )
        return True
    
    # Сохраняем информацию о платеже
    save_payment_photo(user_id, photo_url)
    
    # Получаем имя спонсора
    sponsor = get_sponsor(user_id)
    sponsor_name = sponsor['name'] if sponsor else f"id{user_id}"
    
    # Отправляем админам
    for admin_id in ADMIN_IDS:
        vk.messages.send(
            user_id=admin_id,
            message=f"📸 НОВАЯ ОПЛАТА!\n\n👤 Имя: {sponsor_name}\n🆔 ID: {user_id}\n\n📷 Фото подтверждения: {photo_url}",
            random_id=0
        )
    
    # Подтверждаем пользователю
    waiting_for_photo.pop(user_id, None)
    vk.messages.send(
        user_id=user_id,
        message="✅ Фото получено! Администратор проверит оплату в ближайшее время.",
        keyboard=get_sponsor_keyboard().get_keyboard(),
        random_id=0
    )
    
    return True

def handle_unsubscribe(vk, event):
    """Отписка от спонсорства"""
    user_id = event.user_id
    
    # Запрашиваем подтверждение
    keyboard = VkKeyboard(inline=True)
    keyboard.add_button("✅ Да", color=VkKeyboardColor.POSITIVE, payload={"action": "confirm_unsubscribe", "user_id": user_id})
    keyboard.add_button("❌ Нет", color=VkKeyboardColor.NEGATIVE, payload={"action": "cancel"})
    
    vk.messages.send(
        user_id=user_id,
        message="⚠️ Вы уверены, что хотите отписаться от спонсорства?\n\nПосле отписки вы больше не будете получать уведомления о новых периодах.",
        keyboard=keyboard.get_keyboard(),
        random_id=0
    )

def confirm_unsubscribe(vk, event, user_id):
    """Подтверждение отписки"""
    from database.db import remove_sponsor
    
    remove_sponsor(user_id)
    
    vk.messages.send(
        user_id=user_id,
        message="❌ Вы отписались от спонсорства.\n\nЕсли передумаете, всегда можете нажать 'Стать спонсором клуба' снова.",
        keyboard=get_main_keyboard().get_keyboard(),
        random_id=0
    )