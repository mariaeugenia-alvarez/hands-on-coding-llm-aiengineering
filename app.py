"""Servidor Flask - Nutrition Bot RAG"""

import os
import json
from flask import Flask, request, abort
from handlers.message_orchestrator import handle_message

app = Flask(__name__)

# Secret token para validar que los webhooks vienen de Telegram
# Se configura al registrar el webhook con setWebhook(secret_token=...)
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET_TOKEN", "")


@app.route("/webhook", methods=["POST"])
def webhook():
    """Recibe mensajes de Telegram con validación de origen"""
    # Verificar que la petición viene de Telegram (secret_token)
    if WEBHOOK_SECRET:
        token = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if token != WEBHOOK_SECRET:
            abort(403)

    update = request.get_json()
    handle_message(update)
    return json.dumps({"status": "ok"})


@app.route("/health", methods=["GET"])
def health():
    """Health check"""
    return json.dumps({"status": "ok"})


if __name__ == "__main__":
    print("Servidor: http://localhost:5001/webhook")
    print("Ejecuta: ngrok http 5001")
    debug = os.getenv("DEBUG", "False").lower() == "true"
    app.run(host="0.0.0.0", port=5001, debug=debug)
