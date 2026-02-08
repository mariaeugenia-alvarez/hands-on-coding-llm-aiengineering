"""
Message Orchestrator - Cerebro central del bot

Este es el punto de entrada principal que:
1. Recibe mensajes de Telegram
2. Aplica guardrails de entrada (prompt injection, off-topic)
3. Determina el estado del usuario
4. Enruta a: onboarding / weekly_setup / active / commands
5. Gestiona contexto (RAG + historial + perfil)
6. Aplica guardrails de salida (fuga de datos sensibles)
7. Guarda todo en base de datos
"""

import os
import sys

# Agregar directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.telegram import send_message
from database.db_setup import (
 get_user,
 create_user,
 get_user_profile,
 save_conversation_message,
 get_conversation_history
)
from handlers.onboarding_handler import OnboardingHandler
from services.rag_service import RAGService
from services.llm_service import get_response_with_context
from services.guardrails_service import validate_input, validate_output, is_off_topic
from utils.formatters import format_welcome


# Inicializar RAG Service (singleton)
print(" Inicializando RAG Service en Message Orchestrator...")
rag_service = RAGService()
print(" RAG Service listo\n")


def handle_message(update: dict):
    """
    Punto de entrada principal para procesar mensajes de Telegram

    Args:
        update: Dict con la actualización de Telegram
    """
    if "message" not in update:
        return

    message = update["message"]
    chat_id = str(message["chat"]["id"])
    text = message.get("text", "").strip()

    if not text:
        return

    print(f"\n Mensaje de {chat_id}: {text[:50]}...")

    try:
        # Guardar mensaje del usuario en DB
        save_conversation_message(chat_id, "user", text)

        # Obtener o crear usuario
        user = get_user(chat_id)

        if not user:
            # Usuario nuevo - crear y empezar onboarding
            print(f" → Nuevo usuario: {chat_id}")
            create_user(chat_id, estado='onboarding')
            user = get_user(chat_id)

        estado = user['estado']
        print(f" → Estado: {estado}")

        # --- GUARDRAILS: Validacion de entrada ---
        # Solo aplicar guardrails en estados que usan LLM (no en onboarding ni comandos)
        if estado in ('weekly_setup', 'active') and not text.startswith('/'):
            # 1. Detectar prompt injection
            is_valid, rejection_msg = validate_input(text)
            if not is_valid:
                print(f" Guardrail: Input rechazado (prompt injection)")
                response = rejection_msg
                save_conversation_message(chat_id, "assistant", response)
                send_message(chat_id, response)
                return

            # 2. Detectar off-topic
            off_topic, redirect_msg = is_off_topic(text)
            if off_topic:
                print(f" Guardrail: Input rechazado (off-topic)")
                response = redirect_msg
                save_conversation_message(chat_id, "assistant", response)
                send_message(chat_id, response)
                return

        # Routing según estado
        if estado == 'onboarding':
            response = handle_onboarding(chat_id, text)

        elif estado == 'weekly_setup':
            response = handle_weekly_setup(chat_id, text)

        elif estado == 'active':
            # Verificar si es un comando
            if text.startswith('/'):
                response = handle_command(chat_id, text)
            else:
                response = handle_active_conversation(chat_id, text)

        else:
            response = "Estado desconocido. Usa /start para reiniciar."

        # --- GUARDRAILS: Validacion de salida ---
        response = validate_output(response)

        # Guardar respuesta del assistant en DB
        save_conversation_message(chat_id, "assistant", response)

        # Enviar respuesta a Telegram
        send_message(chat_id, response)

    except Exception as e:
        print(f" Error en handle_message: {e}")
        import traceback
        traceback.print_exc()
        send_message(chat_id, f"Lo siento, ocurrio un error. Intenta de nuevo.")


def handle_onboarding(chat_id: str, text: str) -> str:
    """
    Maneja el flujo de onboarding

    Args:
        chat_id: ID del chat
        text: Mensaje del usuario

    Returns:
        Respuesta para el usuario
    """
    print(" → Handler: Onboarding")

    handler = OnboardingHandler(chat_id)

    # Verificar si es /start
    if text.lower() == '/start':
        response, _ = handler.start_onboarding(), False
        return response

    # Procesar paso del onboarding
    response, completed = handler.process_step(text)

    if completed:
        print(" Onboarding completado → Transición a weekly_setup")

    return response


def handle_weekly_setup(chat_id: str, text: str) -> str:
    """
    Maneja el setup de deportes semanales

    Args:
        chat_id: ID del chat
        text: Mensaje del usuario

    Returns:
        Respuesta para el usuario
    """
    print(" → Handler: Weekly Setup")

    # TODO: Implementar en Día 4
    # Por ahora, usar LLM para guiar al usuario

    user = get_user(chat_id)
    profile = get_user_profile(chat_id)
    history = get_conversation_history(chat_id, limit=10)

    response = get_response_with_context(
        estado='weekly_setup',
        user_message=text,
        user_profile=profile,
        history=history
    )

    # TODO: Parsear deportes y cuando esté completo:
    # - Guardar en weekly_schedules
    # - Cambiar estado a 'active'
    # - Generar plan semanal y suplementos

    return response


def handle_active_conversation(chat_id: str, text: str) -> str:
    """
    Maneja conversación normal con usuario activo

    Usa RAG si la pregunta es sobre nutrición

    Args:
        chat_id: ID del chat
        text: Mensaje del usuario

    Returns:
        Respuesta para el usuario
    """
    print(" → Handler: Active Conversation")

    user = get_user(chat_id)
    profile = get_user_profile(chat_id)
    history = get_conversation_history(chat_id, limit=10)

    # Determinar si usar RAG
    use_rag = should_use_rag(text)

    rag_context = ""
    if use_rag:
        print(" → Usando RAG")
        # Buscar en knowledge base
        rag_results = rag_service.search_knowledge(text, k=3)
        if rag_results:
            rag_context = "\n\n".join([
                f"[Info relevante {i}]\n{chunk}"
                for i, chunk in enumerate(rag_results, 1)
            ])

    # Obtener respuesta del LLM
    response = get_response_with_context(
        estado='active',
        user_message=text,
        user_profile=profile,
        history=history,
        rag_context=rag_context
    )

    return response


def handle_command(chat_id: str, text: str) -> str:
    """
    Maneja comandos especiales (/revision, /plan, etc.)

    Args:
        chat_id: ID del chat
        text: Comando del usuario

    Returns:
        Respuesta para el usuario
    """
    print(f" → Handler: Command ({text})")

    command = text.lower().split()[0]

    if command == '/start':
        # Reiniciar onboarding
        handler = OnboardingHandler(chat_id)
        response, _ = handler.start_onboarding(), False
        return response

    elif command == '/macros':
        # Mostrar macros actuales
        profile = get_user_profile(chat_id)
        if not profile:
            return "No tienes un perfil configurado. Usa /start para comenzar."

        from utils.formatters import format_macros
        return format_macros(profile)

    elif command == '/plan':
        # TODO: Implementar en Día 4
        return "Comando /plan: Ver tu plan semanal (proximamente...)"

    elif command == '/recetas':
        # TODO: Implementar en Día 4
        return "Comando /recetas: Buscar recetas por deporte (proximamente...)"

    elif command == '/suplementos':
        # TODO: Implementar en Día 4
        return "Comando /suplementos: Ver suplementos recomendados (proximamente...)"

    elif command == '/revision':
        # TODO: Implementar en Día 4
        return "Comando /revision: Hacer revision de progreso (proximamente...)"

    elif command == '/help':
        return """Comandos disponibles:

/start - Reiniciar configuracion
/macros - Ver tus macros actuales
/plan - Ver plan semanal
/recetas - Buscar recetas
/suplementos - Ver suplementos
/revision - Revision de progreso
/help - Mostrar esta ayuda

O simplemente preguntame sobre nutricion deportiva!"""

    else:
        return f"Comando desconocido: {command}. Usa /help para ver comandos disponibles."


def should_use_rag(text: str) -> bool:
    """
    Determina si una pregunta debe usar RAG

    Args:
        text: Mensaje del usuario

    Returns:
        True si debe usar RAG
    """
    rag_keywords = [
        'como', 'cuanto', 'que es', 'que son', 'calculo', 'calcular',
        'formula', 'proteina', 'carbohidrato', 'grasa', 'caloria',
        'macro', 'nutriente', 'deficit', 'superavit', 'mantenimiento',
        'suplemento', 'creatina', 'whey', 'omega', 'vitamina',
        'dieta', 'alimentacion', 'comida', 'menu'
    ]

    text_lower = text.lower()
    return any(keyword in text_lower for keyword in rag_keywords)
