# utils/helpers.py

def send_message(vk, user_id, message, keyboard=None):
    """Отправляет сообщение пользователю"""
    params = {
        'user_id': user_id,
        'message': message,
        'random_id': 0
    }
    
    if keyboard is not None:
        if hasattr(keyboard, 'get_keyboard'):
            params['keyboard'] = keyboard.get_keyboard()
        else:
            params['keyboard'] = keyboard
    
    try:
        vk.messages.send(**params)
    except Exception as e:
        print(f"Ошибка отправки сообщения {user_id}: {e}")


def extract_photo_url(attachments):
    """Извлекает URL фото из вложения VK"""
    if not attachments:
        return None
    
    for attachment in attachments:
        if attachment.get('type') == 'photo':
            photo = attachment.get('photo', {})
            sizes = photo.get('sizes', [])
            if sizes:
                # Ищем максимальный размер
                for size in sizes:
                    if size.get('type') in ['w', 'z', 'y', 'x']:
                        return size.get('url')
                return sizes[-1].get('url')
    return None


def extract_photo_id(attachments):
    """Извлекает photo_id из вложения VK"""
    if not attachments:
        return None
    
    for attachment in attachments:
        if attachment.get('type') == 'photo':
            photo = attachment.get('photo', {})
            owner_id = photo.get('owner_id')
            photo_id = photo.get('id')
            access_key = photo.get('access_key', '')
            
            if owner_id and photo_id:
                if access_key:
                    return f"{owner_id}_{photo_id}_{access_key}"
                return f"{owner_id}_{photo_id}"
    return None