"""Handler de mensajes"""

import os
from anthropic import Anthropic
from api.telegram import send_message

# Inicializar cliente de Anthropic
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Historial de conversaciones por chat_id
conversation_history = {}


def handle_message(update):
    """Procesa actualizaciones de Telegram"""
    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"].get("text", "")

        # Llamar a Anthropic con historial
        response_text = get_anthropic_response(chat_id, text)
        send_message(chat_id, response_text)


def get_anthropic_response(chat_id, text):
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

    # Inicializar historial si no existe
    if chat_id not in conversation_history:
        conversation_history[chat_id] = []

    # Agregar mensaje del usuario
    conversation_history[chat_id].append({"role": "user", "content": text})

    # Limitar historial a últimos 10 mensajes
    if len(conversation_history[chat_id]) > 10:
        conversation_history[chat_id] = conversation_history[chat_id][-10:]

    try:
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1024,
            system=system_prompt,
            messages=conversation_history[chat_id],
        )

        response_text = message.content[0].text

        # Agregar respuesta del asistente al historial
        conversation_history[chat_id].append(
            {"role": "assistant", "content": response_text}
        )

        return response_text
    except Exception as e:
        return f"Error: {str(e)}"
