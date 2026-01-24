"""Configuración"""

import os

from dotenv import load_dotenv


# Carga variables definidas en .env
load_dotenv()

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
