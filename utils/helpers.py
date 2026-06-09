# utils/helpers.py
import time

# utils/helpers.py
def send_message(vk, peer_id, message, keyboard=None):
    """
    Отправляет сообщение в диалог (ЛС или беседу)
    peer_id: id пользователя или id беседы (2000000000 + chat_id)
    """
    params = {
        'peer_id': peer_id,  # используем peer_id вместо user_id
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
        print(f"Ошибка отправки сообщения в диалог {peer_id}: {e}")


def extract_photo_url(attachments):
    if not attachments:
        return None
    for attachment in attachments:
        if attachment.get('type') == 'photo':
            sizes = attachment['photo'].get('sizes', [])
            if sizes:
                # берём самое большое (обычно последний элемент)
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