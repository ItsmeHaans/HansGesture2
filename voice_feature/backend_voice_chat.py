# backend_voice_chat.py
from .chatbot_voice import VoiceChatBot

API_KEY = "API"

# Function call untuk frontend
def run_voice_chat():
    """
    Dipanggil dari frontend, menjalankan voice chatbot 1 sesi.
    Mengembalikan (user_text, ai_reply)
    """
    result = {"user": "", "ai": ""}

    def chat_callback(user_text, ai_reply):
        result["user"] = user_text
        result["ai"] = ai_reply

    bot = VoiceChatBot(API_KEY)
    bot.start_chat(callback=chat_callback)

    return result   # frontend tinggal ambil result["ai"]

