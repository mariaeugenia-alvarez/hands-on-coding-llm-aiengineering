"""Servidor Flask - Nutrition Bot RAG"""

import json
from flask import Flask, request
from handlers.message_orchestrator import handle_message

app = Flask(__name__)


@app.route("/webhook", methods=["POST"])
def webhook():
    """Recibe mensajes de Telegram"""
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
    app.run(host="0.0.0.0", port=5001, debug=True)
