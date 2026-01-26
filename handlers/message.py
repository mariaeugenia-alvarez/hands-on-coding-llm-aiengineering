"""Handler de mensajes"""

import os
from anthropic import Anthropic
from api.telegram import send_message

# Inicializar cliente de Anthropic
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def handle_message(update):
    """Procesa actualizaciones de Telegram"""
    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"].get("text", "")

        # Llamar a Anthropic
        response_text = get_anthropic_response(text)
        send_message(chat_id, response_text)


def get_anthropic_response(text):
    """Obtiene respuesta de Anthropic Claude"""
    system_prompt = """Eres una persona experta en nutrición deportiva con más de 15 años de experiencia.

Tu tarea es proponer menús de comida diaria según el deporte a realizar ese día, optimizados según el objetivo del usuario (mantenimiento, déficit, rendimiento).

Debes incluir en tus respuestas:
- Macros que debe contener cada comida del día (desayuno/comida/cena)
- Cantidad y calorías de cada comida

Formato: Mantén un diálogo conversacional con el usuario
Estilo: Conversacional
Tono: Informativo

Contexto importante: La persona que te consulta quiere perder 10 kg en seis meses, optimizando la pérdida de grasa, minimizando la pérdida de músculo y manteniendo el rendimiento deportivo."""

    try:
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": text}],
        )
        return message.content[0].text
    except Exception as e:
        return f"Error: {str(e)}"
