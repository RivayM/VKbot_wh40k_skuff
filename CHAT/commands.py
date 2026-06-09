# CHAT/commands.py
import threading
import re
from .user_state import set_user_faction, get_user_data
from .gemini_handler import process_chat_request

def register_chat_commands(vk):
    print("[DEBUG] register_chat_commands вызвана")
    
    def handle_faction(user_id, peer_id, text, send_message):
        print(f"[DEBUG] handle_faction: user={user_id}, peer={peer_id}")
        new_faction = text[9:].strip()
        if new_faction:
            set_user_faction(user_id, new_faction)
            send_message(vk, peer_id, f"⚔️ Фракция сохранена: {new_faction}")
        else:
            send_message(vk, peer_id, "❌ Напиши: фракция ТвояФракция")

    def handle_chat(user_id, peer_id, text, send_message):
        """Обработка запроса к Gemini"""
        print(f"[DEBUG] handle_chat: user={user_id}, peer={peer_id}, text={text[:50]}")
        
        # Очищаем текст от упоминания бота
        clean_text = re.sub(r'\[club\d+\|"[^"]+"\]\s*', '', text).strip()
        
        if clean_text.startswith("!ask "):
            clean_text = clean_text[5:].strip()
        if clean_text.startswith("бот,"):
            clean_text = clean_text[4:].strip()
        
        if not clean_text:
            send_message(vk, peer_id, "❌ Напиши вопрос после обращения к боту.")
            return
        
        send_message(vk, peer_id, "🧠 Обращаюсь к духу машин... Подожди немного, воин.")
        
        threading.Thread(
            target=process_chat_request,
            args=(vk, user_id, peer_id, clean_text, send_message, get_user_data),
            daemon=True
        ).start()

    return {"фракция": handle_faction, "чат": handle_chat}