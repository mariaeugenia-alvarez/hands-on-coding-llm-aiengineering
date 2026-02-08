"""
Guardrails Service - Validacion de entrada y salida del LLM

Protege el bot contra:
- Prompt injection (manipulacion del comportamiento del LLM)
- Fuga de datos sensibles (estructura DB, API keys, rutas)
- Preguntas fuera de tema (off-topic)
"""

import re
from typing import Tuple


# Patrones de prompt injection (espanol e ingles)
INJECTION_PATTERNS = [
    "ignora tus instrucciones",
    "ignore your instructions",
    "ignora las instrucciones",
    "actua como",
    "act as",
    "pretend you are",
    "finge que eres",
    "finge ser",
    "olvida todo",
    "forget everything",
    "olvida tus reglas",
    "system prompt",
    "system message",
    "nueva personalidad",
    "new personality",
    "modo desarrollador",
    "developer mode",
    "jailbreak",
    "repite tu prompt",
    "repeat your prompt",
    "cuales son tus instrucciones",
    "what are your instructions",
    "muestra tu configuracion",
    "show your configuration",
    "dime tu prompt",
    "tell me your prompt",
    "cambia tu rol",
    "change your role",
]

# Patrones que indican intento de acceder a datos internos
DATA_ACCESS_PATTERNS = [
    "base de datos",
    "database",
    "tabla sql",
    "sql query",
    "schema",
    "estructura de datos",
    "api key",
    "clave api",
    "token de telegram",
    "codigo fuente",
    "source code",
    "mostrar usuarios",
    "show users",
    "datos de otros usuarios",
    "informacion de otros",
]

# Patrones sensibles en la salida del LLM (regex)
SENSITIVE_OUTPUT_PATTERNS = [
    r"SELECT\s+.*\s+FROM",
    r"CREATE\s+TABLE",
    r"INSERT\s+INTO",
    r"DELETE\s+FROM",
    r"UPDATE\s+.*\s+SET",
    r"\buser_profiles\b",
    r"\bconversation_history\b",
    r"\bweekly_schedules\b",
    r"\bonboarding_progress\b",
    r"\buser_revisions\b",
    r"chat_id\s*=",
    r"ANTHROPIC_API_KEY",
    r"TELEGRAM_BOT_TOKEN",
    r"claude-3.*haiku",
    r"claude-3.*sonnet",
    r"/Users/.*\.(py|db|json)",
    r"sqlite3?\s+",
    r"\.fetchone\(\)",
    r"\.fetchall\(\)",
    r"conn\.execute",
]

# Categorias off-topic con palabras clave
OFF_TOPIC_CATEGORIES = {
    "politica": ["politica", "elecciones", "gobierno", "partido", "presidente", "votar", "democracia"],
    "programacion": ["programar", "javascript", "html", "css", "bug", "compilar", "framework", "react", "angular"],
    "matematicas": ["ecuacion", "derivada", "integral", "algebra", "geometria", "trigonometria", "teorema"],
    "entretenimiento": ["pelicula", "serie", "musica", "videojuego", "netflix", "spotify", "concierto"],
    "finanzas": ["invertir", "acciones", "criptomoneda", "bitcoin", "bolsa", "forex", "trading"],
    "religion": ["religion", "iglesia", "rezar", "biblia", "dios", "fe religiosa"],
    "legal": ["abogado", "demanda", "juicio", "ley", "tribunal", "contrato legal"],
}

# Palabras que NO deben disparar off-topic aunque coincidan parcialmente
# (ej: "proteina" contiene "ina" pero no es off-topic)
SAFE_NUTRITION_WORDS = [
    "proteina", "carbohidrato", "grasa", "caloria", "macro", "micro",
    "dieta", "nutricion", "suplemento", "vitamina", "mineral",
    "deporte", "ejercicio", "entrenamiento", "gym", "crossfit",
    "running", "ciclismo", "natacion", "musculo", "peso",
    "desayuno", "comida", "cena", "snack", "receta", "alimento",
    "creatina", "whey", "omega", "cafeina", "hierro", "zinc",
    "deficit", "superavit", "mantenimiento", "masa muscular",
    "hidratacion", "agua", "recuperacion", "rendimiento",
    "ayuno", "intermitente", "carga", "descarga",
]


def validate_input(text: str) -> Tuple[bool, str]:
    """
    Valida el mensaje del usuario antes de enviarlo al LLM.

    Detecta:
    - Intentos de prompt injection
    - Intentos de acceder a datos internos del sistema

    Args:
        text: Mensaje del usuario

    Returns:
        Tuple (es_valido, mensaje_de_rechazo)
        - (True, "") si el mensaje es valido
        - (False, "mensaje") si debe ser rechazado
    """
    text_lower = text.lower().strip()

    # Verificar prompt injection
    for pattern in INJECTION_PATTERNS:
        if pattern in text_lower:
            return (False, "Soy tu nutricionista deportivo y solo puedo ayudarte con temas de nutricion y deporte. Como puedo ayudarte con tu alimentacion?")

    # Verificar acceso a datos internos
    for pattern in DATA_ACCESS_PATTERNS:
        if pattern in text_lower:
            # Excepcion: si tambien contiene palabras de nutricion, probablemente es legitimo
            if any(safe in text_lower for safe in SAFE_NUTRITION_WORDS):
                continue
            return (False, "No puedo compartir informacion tecnica del sistema. Soy tu nutricionista deportivo, preguntame sobre dietas, macros o suplementos!")

    return (True, "")


def is_off_topic(text: str) -> Tuple[bool, str]:
    """
    Detecta si el mensaje es sobre un tema fuera del ambito de nutricion deportiva.

    Primera barrera rapida ANTES de llamar al LLM (ahorra tokens).

    Args:
        text: Mensaje del usuario

    Returns:
        Tuple (es_off_topic, mensaje_redireccion)
        - (False, "") si el tema es valido
        - (True, "mensaje") si es off-topic
    """
    text_lower = text.lower().strip()

    # Si contiene palabras de nutricion, no es off-topic
    if any(safe in text_lower for safe in SAFE_NUTRITION_WORDS):
        return (False, "")

    # Si es muy corto (saludo, etc.), dejar pasar
    if len(text_lower.split()) <= 3:
        return (False, "")

    # Verificar categorias off-topic
    for category, keywords in OFF_TOPIC_CATEGORIES.items():
        for keyword in keywords:
            if keyword in text_lower:
                return (True, f"Solo puedo ayudarte con temas de nutricion deportiva. No puedo opinar sobre {category}. Preguntame sobre dietas, macros, suplementos o alimentacion para tu deporte!")

    return (False, "")


def validate_output(response: str) -> str:
    """
    Valida la respuesta del LLM antes de enviarla al usuario.

    Detecta fugas accidentales de datos sensibles como:
    - Queries SQL
    - Nombres de tablas de la DB
    - API keys o tokens
    - Rutas del sistema

    Args:
        response: Respuesta generada por el LLM

    Returns:
        La respuesta original si es segura, o un mensaje generico si detecta fuga
    """
    for pattern in SENSITIVE_OUTPUT_PATTERNS:
        if re.search(pattern, response, re.IGNORECASE):
            return "Lo siento, hubo un problema al generar la respuesta. Podrias reformular tu pregunta sobre nutricion deportiva?"

    return response
