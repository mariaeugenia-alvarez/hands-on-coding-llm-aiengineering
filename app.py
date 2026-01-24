"""Servidor Flask"""

import json
from flask import Flask, request
from handlers.webhook import handle_webhook

app = Flask(__name__)


@app.route("/webhook", methods=["POST"])
def webhook():
    """Recibe mensajes de Telegram"""
    update = request.get_json()
    return handle_webhook(update)


@app.route("/health", methods=["GET"])
def health():
    """Health check"""
    return json.dumps({"status": "ok"})


if __name__ == "__main__":
    print("Servidor: http://localhost:5000/webhook")
    print("Ejecuta: ngrok http 5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
