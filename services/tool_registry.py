"""
Tool Registry - Registro centralizado de herramientas para el agente

Define las tools en formato estándar (JSON Schema) y las conecta con
las funciones de tools_service.py. El agente usa este registro para:
1. Enviar las definiciones al LLM (para que decida cuál usar)
2. Ejecutar la tool seleccionada por el LLM
"""

import json
from typing import Dict, List, Optional
from services.tools_service import (
    calcular_macros_objetivo,
    buscar_recetas_por_deporte,
    generar_menu_diario,
    recomendar_suplementos,
    calcular_ajuste_revision,
)


# Definiciones de tools en formato JSON Schema estándar
# Compatible con OpenAI, Anthropic, Mistral, etc.
TOOL_DEFINITIONS = [
    {
        "name": "calcular_macros",
        "description": (
            "Calcula calorias diarias y macronutrientes personalizados "
            "(proteina, carbohidratos, grasas) segun peso, objetivo y nivel de actividad. "
            "Usar cuando el usuario pregunta por sus macros, calorias o quiere recalcular."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "peso_kg": {
                    "type": "number",
                    "description": "Peso del usuario en kilogramos",
                },
                "objetivo": {
                    "type": "string",
                    "enum": ["deficit", "mantenimiento", "superavit"],
                    "description": "Objetivo nutricional del usuario",
                },
                "porcentaje": {
                    "type": "integer",
                    "description": "Porcentaje de ajuste (ej: 10, 20, 30 para deficit; 10, 15, 20 para superavit)",
                },
                "factor_actividad": {
                    "type": "number",
                    "description": "Factor de actividad fisica: 1.2 (sedentario), 1.4 (ligero), 1.6 (moderado), 1.8 (intenso), 2.0 (muy intenso)",
                },
            },
            "required": ["peso_kg", "objetivo", "porcentaje", "factor_actividad"],
        },
    },
    {
        "name": "buscar_recetas",
        "description": (
            "Busca recetas de comida ideales para un deporte especifico. "
            "Usar cuando el usuario pide recetas, ideas de comida o menu para su deporte."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "deporte": {
                    "type": "string",
                    "description": "Nombre del deporte (ej: gym, crossfit, running, natacion, ciclismo)",
                },
            },
            "required": ["deporte"],
        },
    },
    {
        "name": "generar_menu_diario",
        "description": (
            "Genera un menu completo para un dia (desayuno, comida, cena, snacks) "
            "con calorias distribuidas y recetas sugeridas. "
            "Usar cuando el usuario pide un plan de comidas o menu del dia."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "calorias_objetivo": {
                    "type": "integer",
                    "description": "Calorias objetivo diarias del usuario",
                },
                "proteina_g": {
                    "type": "number",
                    "description": "Gramos de proteina diarios objetivo",
                },
                "carbos_g": {
                    "type": "number",
                    "description": "Gramos de carbohidratos diarios objetivo",
                },
                "grasas_g": {
                    "type": "number",
                    "description": "Gramos de grasas diarios objetivo",
                },
                "deporte": {
                    "type": "string",
                    "description": "Deporte que practica ese dia",
                },
            },
            "required": ["calorias_objetivo", "proteina_g", "carbos_g", "grasas_g", "deporte"],
        },
    },
    {
        "name": "recomendar_suplementos",
        "description": (
            "Recomienda suplementos deportivos personalizados con dosis calculadas "
            "segun peso, edad, sexo, objetivo y deportes. "
            "Usar cuando el usuario pregunta por suplementos, creatina, proteina whey, etc."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "peso_kg": {
                    "type": "number",
                    "description": "Peso del usuario en kg",
                },
                "edad": {
                    "type": "integer",
                    "description": "Edad del usuario",
                },
                "sexo": {
                    "type": "string",
                    "enum": ["M", "F"],
                    "description": "Sexo del usuario",
                },
                "objetivo": {
                    "type": "string",
                    "enum": ["deficit", "mantenimiento", "superavit"],
                    "description": "Objetivo nutricional",
                },
                "deportes_semana": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Lista de deportes que practica en la semana",
                },
            },
            "required": ["peso_kg", "edad", "sexo", "objetivo", "deportes_semana"],
        },
    },
    {
        "name": "calcular_ajuste_revision",
        "description": (
            "Calcula ajustes de macros basandose en el progreso semanal del usuario. "
            "Usar cuando el usuario reporta su peso actual para revision de progreso."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "peso_actual": {
                    "type": "number",
                    "description": "Peso actual del usuario en kg",
                },
                "peso_anterior": {
                    "type": "number",
                    "description": "Peso en la revision anterior en kg",
                },
                "objetivo": {
                    "type": "string",
                    "enum": ["deficit", "mantenimiento", "superavit"],
                    "description": "Objetivo nutricional actual",
                },
                "feedback": {
                    "type": "string",
                    "description": "Feedback del usuario sobre como se siente",
                },
            },
            "required": ["peso_actual", "peso_anterior", "objetivo", "feedback"],
        },
    },
]

# Mapa de nombre de tool → función ejecutable
_TOOL_EXECUTORS = {
    "calcular_macros": lambda args: calcular_macros_objetivo(
        peso_kg=args["peso_kg"],
        objetivo=args["objetivo"],
        porcentaje=args["porcentaje"],
        factor_actividad=args["factor_actividad"],
    ),
    "buscar_recetas": lambda args: buscar_recetas_por_deporte(
        deporte=args["deporte"],
    ),
    "generar_menu_diario": lambda args: generar_menu_diario(
        calorias_objetivo=args["calorias_objetivo"],
        macros={
            "proteina_g": args["proteina_g"],
            "carbos_g": args["carbos_g"],
            "grasas_g": args["grasas_g"],
        },
        deporte=args["deporte"],
    ),
    "recomendar_suplementos": lambda args: recomendar_suplementos(
        peso_kg=args["peso_kg"],
        edad=args["edad"],
        sexo=args["sexo"],
        objetivo=args["objetivo"],
        deportes_semana=args["deportes_semana"],
    ),
    "calcular_ajuste_revision": lambda args: calcular_ajuste_revision(
        peso_actual=args["peso_actual"],
        peso_anterior=args["peso_anterior"],
        objetivo=args["objetivo"],
        feedback=args["feedback"],
    ),
}


def get_tool_definitions() -> List[Dict]:
    """Devuelve las definiciones de tools para enviar al LLM"""
    return TOOL_DEFINITIONS


def execute_tool(name: str, arguments: dict) -> str:
    """
    Ejecuta una tool por nombre y devuelve el resultado como string JSON.

    Args:
        name: Nombre de la tool (debe coincidir con TOOL_DEFINITIONS)
        arguments: Argumentos parseados del LLM

    Returns:
        Resultado de la tool serializado como JSON string
    """
    executor = _TOOL_EXECUTORS.get(name)
    if not executor:
        return json.dumps({"error": f"Tool '{name}' no encontrada"})

    try:
        result = executor(arguments)
        return json.dumps(result, ensure_ascii=False, default=str)
    except Exception as e:
        return json.dumps({"error": f"Error ejecutando {name}: {str(e)}"})
