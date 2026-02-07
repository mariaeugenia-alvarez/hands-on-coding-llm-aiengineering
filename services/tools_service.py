"""
Tools Service - Herramientas de cálculo para el bot nutricionista

5 tools core:
1. calcular_macros_objetivo - Calcula calorías y macros personalizados
2. buscar_recetas_por_deporte - Busca recetas según deporte
3. generar_menu_diario - Genera menú completo para un día
4. recomendar_suplementos - Recomendación personalizada de suplementos
5. calcular_ajuste_revision - Calcula ajustes en revisión semanal
"""

import os
import json
from typing import Optional

# Paths a archivos de datos
DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"
)
RECETAS_PATH = os.path.join(DATA_DIR, "recetas.json")
DEPORTES_PATH = os.path.join(DATA_DIR, "deportes_config.json")
ALIMENTOS_PATH = os.path.join(DATA_DIR, "alimentos.json")


def _load_json(filepath: str) -> dict:
    """Carga un archivo JSON"""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def calcular_macros_objetivo(
    peso_kg: float, objetivo: str, porcentaje: int, factor_actividad: float
) -> dict:
    """
    Calcula calorías y macros según fórmula de guia_macros.md

    Args:
        peso_kg: Peso del usuario en kg
        objetivo: 'deficit', 'mantenimiento', o 'superavit'
        porcentaje: Porcentaje de ajuste
        factor_actividad: Factor de actividad (1.2 a 2.0)

    Returns:
        Dict con calorias_objetivo, proteina_g, carbos_g, grasas_g
    """
    calorias_mantenimiento = peso_kg * 22 * factor_actividad

    if objetivo == "deficit":
        calorias_objetivo = calorias_mantenimiento * (1 - porcentaje / 100)
        proteina_g = peso_kg * 2.5
        grasas_g = peso_kg * 0.5
    elif objetivo == "superavit":
        calorias_objetivo = calorias_mantenimiento * (1 + porcentaje / 100)
        proteina_g = peso_kg * 2.0
        grasas_g = peso_kg * 1.0
    else:  # mantenimiento
        calorias_objetivo = calorias_mantenimiento
        proteina_g = peso_kg * 2.0
        grasas_g = peso_kg * 0.8

    # Carbos = calorías restantes / 4
    calorias_restantes = calorias_objetivo - (proteina_g * 4) - (grasas_g * 9)
    carbos_g = max(calorias_restantes / 4, 0)

    return {
        "calorias_mantenimiento": round(calorias_mantenimiento),
        "calorias_objetivo": round(calorias_objetivo),
        "proteina_g": round(proteina_g),
        "carbos_g": round(carbos_g),
        "grasas_g": round(grasas_g),
        "objetivo": objetivo,
        "porcentaje": porcentaje,
        "factor_actividad": factor_actividad,
    }


def buscar_recetas_por_deporte(deporte: str, max_results: int = 5) -> list:
    """
    Busca recetas ideales para un deporte

    Args:
        deporte: Nombre del deporte
        max_results: Número máximo de recetas

    Returns:
        Lista de recetas filtradas
    """
    data = _load_json(RECETAS_PATH)
    recetas = data.get("recetas", [])

    # Filtrar por deporte
    filtered = [
        r
        for r in recetas
        if deporte.lower() in [d.lower() for d in r.get("ideal_para", [])]
    ]

    if not filtered:
        filtered = recetas

    return filtered[:max_results]


def generar_menu_diario(calorias_objetivo: int, macros: dict, deporte: str) -> dict:
    """
    Genera menú completo para un día

    Args:
        calorias_objetivo: Calorías objetivo del día
        macros: Dict con proteina_g, carbos_g, grasas_g
        deporte: Deporte del día

    Returns:
        Dict con menú del día
    """
    # Cargar config del deporte
    deportes_data = _load_json(DEPORTES_PATH)
    config_deporte = deportes_data["deportes"].get(deporte.lower(), {})

    mult_prot = config_deporte.get("multiplicador_proteina", 1.0)
    mult_carbs = config_deporte.get("multiplicador_carbos", 1.0)

    # Ajustar macros según deporte del día
    proteina_ajustada = round(macros.get("proteina_g", 0) * mult_prot)
    carbos_ajustados = round(macros.get("carbos_g", 0) * mult_carbs)
    grasas = macros.get("grasas_g", 0)

    # Buscar recetas para el deporte
    recetas = buscar_recetas_por_deporte(deporte)

    menu = {
        "deporte_dia": deporte,
        "desayuno": {
            "calorias": round(calorias_objetivo * 0.25),
            "receta_sugerida": (
                recetas[0]["nombre"] if recetas else "Avena con proteina"
            ),
        },
        "comida": {
            "calorias": round(calorias_objetivo * 0.40),
            "receta_sugerida": (
                recetas[1]["nombre"] if len(recetas) > 1 else "Pollo con arroz"
            ),
        },
        "cena": {
            "calorias": round(calorias_objetivo * 0.25),
            "receta_sugerida": (
                recetas[2]["nombre"] if len(recetas) > 2 else "Salmon con verduras"
            ),
        },
        "snacks": {
            "calorias": round(calorias_objetivo * 0.10),
            "sugerencia": "Frutos secos y fruta",
        },
    }

    return menu


def recomendar_suplementos(
    peso_kg: float, edad: int, sexo: str, objetivo: str, deportes_semana: list
) -> list:
    """
    Recomienda suplementos con cálculos personalizados

    Args:
        peso_kg: Peso del usuario en kg
        edad: Edad del usuario
        sexo: 'M' o 'F'
        objetivo: 'deficit', 'mantenimiento', o 'superavit'
        deportes_semana: Lista de deportes que practica

    Returns:
        Lista de suplementos recomendados
    """
    suplementos = []
    deportes_unicos = list(
        set(d.lower() for d in deportes_semana if d and d.lower() != "descanso")
    )

    # 1. Proteína Whey (si hace 3+ días de deporte)
    if len(deportes_semana) >= 3:
        cantidad_proteina = round(peso_kg * 0.35)
        suplementos.append(
            {
                "nombre": "Proteina Whey",
                "cantidad": f"{cantidad_proteina}g",
                "timing": "Post-entrenamiento (30min despues)",
                "razon": f"Ayuda a cumplir los {round(peso_kg * 2.0)}g diarios de proteina",
            }
        )

    # 2. Creatina (si hace ejercicios de fuerza)
    deportes_fuerza = ["gym", "crossfit", "weightlifting", "martial_arts"]
    if any(d in deportes_fuerza for d in deportes_unicos):
        suplementos.append(
            {
                "nombre": "Creatina Monohidrato",
                "cantidad": "5g",
                "timing": "Cualquier momento del dia con comida",
                "razon": "Mejora rendimiento en ejercicios de fuerza y potencia",
            }
        )

    # 3. Omega-3
    cantidad_omega = "2-3g" if edad > 35 or objetivo == "deficit" else "1-2g"
    suplementos.append(
        {
            "nombre": "Omega-3 (EPA/DHA)",
            "cantidad": cantidad_omega,
            "timing": "Con comida principal",
            "razon": "Reduce inflamacion muscular y mejora recuperacion",
        }
    )

    return suplementos


def calcular_ajuste_revision(
    peso_actual: float,
    peso_anterior: float,
    objetivo: str,
    feedback: str,
    macros_actuales: Optional[dict] = None,
) -> dict:
    """
    Calcula ajustes necesarios en una revisión de progreso

    Args:
        peso_actual: Peso actual del usuario
        peso_anterior: Peso en la revisión anterior
        objetivo: 'deficit', 'mantenimiento', o 'superavit'
        feedback: Texto libre del usuario
        macros_actuales: Dict con macros actuales (opcional)

    Returns:
        Dict con cambios recomendados y ajustes de macros
    """
    delta_peso = peso_actual - peso_anterior
    ajustes = {
        "peso_anterior": peso_anterior,
        "peso_actual": peso_actual,
        "delta_peso": round(delta_peso, 1),
        "cambios": [],
        "ajuste_calorias": 0,
        "ajuste_carbos": 0,
    }

    if objetivo == "deficit":
        if delta_peso > 0:
            ajustes["cambios"].append("Subiste de peso. Reduce 150-200 kcal")
            ajustes["ajuste_calorias"] = -175
            ajustes["ajuste_carbos"] = -40
        elif delta_peso < -1.5:
            ajustes["cambios"].append("Perdiste peso muy rapido. Aumenta 100 kcal")
            ajustes["ajuste_calorias"] = 100
            ajustes["ajuste_carbos"] = 25
        elif -1.0 <= delta_peso <= -0.5:
            ajustes["cambios"].append("Perfecto! Sigue asi")
        else:
            ajustes["cambios"].append("Progreso lento. Reduce 50-100 kcal")
            ajustes["ajuste_calorias"] = -75
            ajustes["ajuste_carbos"] = -15

    elif objetivo == "superavit":
        if delta_peso < 0:
            ajustes["cambios"].append("Perdiste peso. Aumenta 200-300 kcal")
            ajustes["ajuste_calorias"] = 250
            ajustes["ajuste_carbos"] = 50
        elif delta_peso > 0.8:
            ajustes["cambios"].append("Subiste mucho. Reduce 100 kcal")
            ajustes["ajuste_calorias"] = -100
            ajustes["ajuste_carbos"] = -25
        else:
            ajustes["cambios"].append("Buen progreso")

    # Análisis de feedback
    if "hambre" in feedback.lower():
        ajustes["cambios"].append("Reportas hambre. Aumenta proteina y vegetales")

    return ajustes
