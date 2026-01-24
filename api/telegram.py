"""Cliente de Telegram"""

import requests
from config.settings import API_URL


def send_message(chat_id, text):
    """Envía un mensaje al chat"""
    print(chat_id)
    requests.post(f"{API_URL}/sendMessage", json={"chat_id": chat_id, "text": text})
