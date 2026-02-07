"""
Text Utilities - Funciones para extraer datos de texto de usuario

Usado principalmente en onboarding y comandos para parsear respuestas del usuario.
"""

import re


def extract_number(text: str) -> float:
    """
    Extrae el primer número de un texto

    Args:
        text: Texto del usuario (ej: "Peso 80 kg", "mido 1.75m", "80")

    Returns:
        Número encontrado o None si no hay
    """
    # Buscar números decimales o enteros
    match = re.search(r'(\d+[.,]\d+|\d+)', text)
    if match:
        number_str = match.group(1).replace(',', '.')
        return float(number_str)
    return None


def extract_sexo(text: str) -> str:
    """
    Extrae sexo del texto del usuario

    Args:
        text: Respuesta del usuario

    Returns:
        'M', 'F', o None
    """
    text_lower = text.lower().strip()

    masculino = ['m', 'masculino', 'hombre', 'macho', 'varon', 'male', 'man']
    femenino = ['f', 'femenino', 'mujer', 'female', 'woman']

    if text_lower in masculino or any(w in text_lower for w in masculino):
        return 'M'
    elif text_lower in femenino or any(w in text_lower for w in femenino):
        return 'F'
    return None


def extract_objetivo(text: str) -> str:
    """
    Extrae objetivo del texto del usuario

    Args:
        text: Respuesta del usuario

    Returns:
        'deficit', 'mantenimiento', 'superavit', o None
    """
    text_lower = text.lower().strip()

    deficit_keywords = ['deficit', 'perder', 'bajar', 'adelgazar', 'quemar', 'grasa', 'secar', 'definir', 'definicion']
    superavit_keywords = ['superavit', 'ganar', 'subir', 'musculo', 'volumen', 'masa', 'bulking']
    mantenimiento_keywords = ['mantenimiento', 'mantener', 'igual', 'estable', 'recomposicion']

    if any(w in text_lower for w in deficit_keywords):
        return 'deficit'
    elif any(w in text_lower for w in superavit_keywords):
        return 'superavit'
    elif any(w in text_lower for w in mantenimiento_keywords):
        return 'mantenimiento'
    return None


def extract_factor_actividad(text: str) -> float:
    """
    Extrae factor de actividad del texto o número directo

    Args:
        text: Respuesta del usuario

    Returns:
        Factor de actividad (1.2 - 2.0) o None
    """
    text_lower = text.lower().strip()

    # Intentar número directo
    number = extract_number(text)
    if number and 1.0 <= number <= 2.5:
        return number

    # Buscar por keyword
    if any(w in text_lower for w in ['sedentario', 'oficina', 'poco', 'nada']):
        return 1.2
    elif any(w in text_lower for w in ['ligera', 'ligero', 'leve', '1-2 dias', 'poco ejercicio']):
        return 1.4
    elif any(w in text_lower for w in ['moderada', 'moderado', '3-4 dias', '3 dias', 'regular']):
        return 1.6
    elif any(w in text_lower for w in ['activa', 'activo', '5-6 dias', '5 dias', 'bastante']):
        return 1.8
    elif any(w in text_lower for w in ['muy activa', 'muy activo', 'todos los dias', 'atleta', 'profesional', 'intenso']):
        return 2.0
    return None


def extract_porcentaje(text: str) -> int:
    """
    Extrae porcentaje de ajuste del texto

    Args:
        text: Respuesta del usuario (ej: "20%", "-20", "moderado")

    Returns:
        Porcentaje como entero positivo (10, 15, 20, 30) o None
    """
    text_lower = text.lower().strip()

    # Número directo
    number = extract_number(text)
    if number and 5 <= number <= 40:
        return int(number)

    # Por keyword
    if any(w in text_lower for w in ['suave', 'ligero', 'poco', 'leve']):
        return 10
    elif any(w in text_lower for w in ['moderado', 'medio', 'normal']):
        return 20
    elif any(w in text_lower for w in ['agresivo', 'fuerte', 'mucho', 'rapido']):
        return 30
    return None


def extract_deporte(text: str) -> str:
    """
    Extrae nombre de deporte del texto del usuario

    Args:
        text: Texto del usuario

    Returns:
        Nombre normalizado del deporte o None
    """
    text_lower = text.lower().strip()

    deportes_map = {
        'crossfit': ['crossfit', 'cross fit', 'cf'],
        'gym': ['gym', 'gimnasio', 'pesas', 'musculacion'],
        'running': ['running', 'correr', 'carrera', 'run', 'trotar', 'jogging'],
        'cycling': ['cycling', 'ciclismo', 'bicicleta', 'bici', 'bike'],
        'swimming': ['swimming', 'natacion', 'nadar', 'piscina'],
        'soccer': ['soccer', 'futbol', 'football'],
        'basketball': ['basketball', 'baloncesto', 'basquet'],
        'yoga': ['yoga'],
        'pilates': ['pilates'],
        'weightlifting': ['weightlifting', 'halterofilia', 'peso olimpico'],
        'triathlon': ['triathlon', 'triatlon'],
        'hiking': ['hiking', 'senderismo', 'montana', 'trekking', 'caminar'],
        'climbing': ['climbing', 'escalada', 'roca'],
        'rowing': ['rowing', 'remo'],
        'martial_arts': ['martial_arts', 'artes marciales', 'mma', 'karate', 'judo', 'bjj', 'jiu jitsu'],
        'dance': ['dance', 'baile', 'bailar', 'zumba'],
        'tennis': ['tennis', 'tenis', 'padel'],
        'badminton': ['badminton'],
        'boxing': ['boxing', 'boxeo']
    }

    for deporte, keywords in deportes_map.items():
        if any(kw in text_lower for kw in keywords):
            return deporte

    return None


def extract_deportes_semana(text: str) -> dict:
    """
    Extrae deportes de la semana de un texto largo

    Args:
        text: Texto del usuario describiendo su semana

    Returns:
        Dict con {dia: deporte} (ej: {"lunes": "gym", "martes": "running"})
    """
    text_lower = text.lower()
    dias = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
    semana = {}

    for dia in dias:
        if dia in text_lower:
            # Buscar el deporte después del nombre del día
            idx = text_lower.index(dia)
            fragment = text_lower[idx:idx + 80]  # Tomar un fragmento después del día

            # Buscar descanso primero
            if any(w in fragment for w in ['descanso', 'libre', 'nada', 'off', 'no entreno']):
                semana[dia] = 'descanso'
            else:
                deporte = extract_deporte(fragment)
                if deporte:
                    semana[dia] = deporte

    return semana


def is_affirmative(text: str) -> bool:
    """Verifica si el texto es una respuesta afirmativa"""
    text_lower = text.lower().strip()
    return text_lower in ['si', 'sí', 's', 'yes', 'y', 'ok', 'dale', 'vale', 'claro',
                          'por supuesto', 'correcto', 'exacto', 'afirmativo', 'confirmo']


def is_negative(text: str) -> bool:
    """Verifica si el texto es una respuesta negativa"""
    text_lower = text.lower().strip()
    return text_lower in ['no', 'n', 'nope', 'nah', 'negativo', 'para nada', 'nel']
