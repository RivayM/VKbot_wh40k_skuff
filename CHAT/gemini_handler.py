# CHAT/gemini_handler.py
import os
import re
import logging
from google import genai
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-2.0-flash-lite"

WARHAMMER_STYLE = """Ты — мрачный и эпичный помощник в стиле вселенной Warhammer 40,000. 
Твои ответы должны быть пафосными, суровыми и немного мрачными. 
Используй обращения вроде «Воин», «Служитель Империума», «Еретик».
Никогда не теряй эту роль."""

client = None

def init_gemini():
    global client
    if GEMINI_API_KEY:
        client = genai.Client(api_key=GEMINI_API_KEY)
        logger.info("✅ Gemini API инициализирован")
    else:
        logger.warning("⚠️ GEMINI_API_KEY не найден")

def get_vk_user_name(vk, user_id):
    """Получает имя пользователя из ВК по ID"""
    try:
        user = vk.users.get(user_ids=user_id)[0]
        return f"{user['first_name']} {user['last_name']}"
    except:
        return f"Пользователь {user_id}"

def extract_mentions(vk, text, get_user_data_func):
    """Извлекает упоминания @ и возвращает строку с именами и фракциями"""
    pattern = r'\[id(\d+)\|([^\]]+)\]'
    matches = re.findall(pattern, text)
    if not matches:
        return "", text
    
    result = []
    for uid, name in matches:
        user_id = int(uid)
        user_name = get_vk_user_name(vk, user_id)
        user_data = get_user_data_func(user_id)
        faction = user_data.get('faction') if user_data else "неизвестная фракция"
        result.append(f"{user_name} (фракция: {faction})")
    
    # Очищаем текст от упоминаний
    clean_text = re.sub(r'\[id\d+\|[^\]]+\]', '', text).strip()
    
    mentions_str = "\nУпомянутые воины:\n" + "\n".join(f"- {r}" for r in result) if result else ""
    return mentions_str, clean_text

def call_gemini(prompt, user_name, faction, mentions_str=""):
    global client
    if not client:
        return "Gemini API не инициализирован."
    
    try:
        context = f"{WARHAMMER_STYLE}\n\nВоин: {user_name}\nФракция: {faction}"
        if mentions_str:
            context += mentions_str
        
        full_prompt = f"{context}\n\nЗапрос: {prompt}"
        
        print(f"[DEBUG GEMINI] Запрос к API: {full_prompt[:200]}...")
        
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=full_prompt
        )
        print(f"[DEBUG GEMINI] Ответ API: {response.text[:200] if response.text else 'НЕТ ТЕКСТА'}")
        return response.text if response.text else "Дух машин молчит..."
    except Exception as e:
        if "429" in str(e):
            return "⚔️ Дух машин перегружен! Квота на сегодня исчерпана. Попробуй завтра, воин."
        print(f"[DEBUG GEMINI] ОШИБКА: {e}")
        return f"Ошибка: {e}"

def process_chat_request(vk, user_id, peer_id, text, send_message_func, get_user_data_func):
    print(f"[DEBUG GEMINI] Начало обработки запроса от {user_id}")
    
    user_name = get_vk_user_name(vk, user_id)
    user_data = get_user_data_func(user_id)
    faction = user_data.get('faction') if user_data else None
    
    if not faction:
        send_message_func(vk, peer_id, "⚔️ Укажи фракцию: фракция [название]")
        return
    
    mentions_str, clean_text = extract_mentions(vk, text, get_user_data_func)
    
    if not clean_text:
        send_message_func(vk, peer_id, "Воин, я не расслышал запрос...")
        return
    
    response = call_gemini(clean_text, user_name, faction, mentions_str)
    send_message_func(vk, peer_id, f"🤖 **Дух машин:**\n{response}")