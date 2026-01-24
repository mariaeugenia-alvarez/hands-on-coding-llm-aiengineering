"""Handler del webhook"""

import json
from api.telegram import send_message


def handle_webhook(update):
    """Procesa actualizaciones de Telegram"""
    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"].get("text", "")

        # Responder al mensaje
        response = f"Recibí: {text}"
        send_message(chat_id, response)
