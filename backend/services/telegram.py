import requests
import telebot

from config import config

def send_telegram_error_message(chat_id, error_text):
    bot_token = config.TELEGRAM_API_KEY
    base_url = f"https://api.telegram.org/bot{bot_token}/"
    
    params = {
        "chat_id": chat_id,
        "text": error_text
    }
    
    response = requests.post(base_url + "sendMessage", json=params)
    return response.json()

def telegram_report_error(resource_name, chat_id, status_code, error_detail):
    user_id = config.TELEGRAM_REPORT_ID
    if (user_id and resource_name and chat_id and status_code and error_detail): 
        error_text = f"{resource_name} : Error reported in chat {chat_id} => ({status_code}) {error_detail}"
        send_telegram_error_message(user_id, error_text)
    
class BotHandler:
    
    def __init__(self, token):
        self.bot = telebot.TeleBot(token)

    def edit_message(self, msg, chat_id, message_id):
        self.bot.edit_message_text(text=msg, chat_id=chat_id, message_id=message_id)
    
    def send_message(self, msg, chat_id):
        self.bot.send_message(chat_id=chat_id, text=msg)

    def __del__(self):
      self.bot.stop_bot()
