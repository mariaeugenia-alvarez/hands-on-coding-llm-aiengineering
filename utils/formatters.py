"""
Formatters - Funciones para formatear mensajes para Telegram

Formatea datos de macros, menús, suplementos, etc. en texto legible para Telegram.
"""


def format_macros(macros: dict) -> str:
    """
    Formatea macros para mostrar en Telegram

    Args:
        macros: Dict con calorias_objetivo, proteina_g, carbos_g, grasas_g

    Returns:
        Texto formateado
    """
    lines = [
        "--- TUS MACROS ---",
        "",
        f"Calorias objetivo: {macros.get('calorias_objetivo', 'N/A')} kcal/dia",
        f"Proteina: {macros.get('proteina_g', 'N/A')}g",
        f"Carbohidratos: {macros.get('carbos_g', 'N/A')}g",
        f"Grasas: {macros.get('grasas_g', 'N/A')}g",
    ]

    if 'calorias_mantenimiento' in macros:
        lines.insert(2, f"Calorias mantenimiento: {macros['calorias_mantenimiento']} kcal")
        lines.insert(3, f"Objetivo: {macros.get('objetivo', 'N/A')} ({macros.get('porcentaje', 'N/A')}%)")
        lines.insert(4, "")

    return "\n".join(lines)


def format_menu(menu: dict) -> str:
    """
    Formatea menú diario para Telegram

    Args:
        menu: Dict del menú generado por generar_menu_diario()

    Returns:
        Texto formateado
    """
    deporte = menu.get('deporte_dia', 'General')
    timing = menu.get('timing_comida', 'N/A')

    lines = [
        f"--- MENU DEL DIA ({deporte.upper()}) ---",
        f"Timing comida pre-entreno: {timing}",
        "",
    ]

    # Desayuno
    d = menu.get('desayuno', {})
    lines.extend([
        "DESAYUNO",
        f"  {d.get('receta_sugerida', 'N/A')}",
        f"  {d.get('calorias', 0)} kcal | P:{d.get('proteina_g', 0)}g C:{d.get('carbos_g', 0)}g G:{d.get('grasas_g', 0)}g",
        "",
    ])

    # Comida
    c = menu.get('comida', {})
    lines.extend([
        "COMIDA",
        f"  {c.get('receta_sugerida', 'N/A')}",
        f"  {c.get('calorias', 0)} kcal | P:{c.get('proteina_g', 0)}g C:{c.get('carbos_g', 0)}g G:{c.get('grasas_g', 0)}g",
        "",
    ])

    # Cena
    ce = menu.get('cena', {})
    lines.extend([
        "CENA",
        f"  {ce.get('receta_sugerida', 'N/A')}",
        f"  {ce.get('calorias', 0)} kcal | P:{ce.get('proteina_g', 0)}g C:{ce.get('carbos_g', 0)}g G:{ce.get('grasas_g', 0)}g",
        "",
    ])

    # Snacks
    s = menu.get('snacks', {})
    lines.extend([
        "SNACKS",
        f"  {s.get('sugerencia', 'Frutos secos y fruta')}",
        f"  {s.get('calorias', 0)} kcal | P:{s.get('proteina_g', 0)}g C:{s.get('carbos_g', 0)}g G:{s.get('grasas_g', 0)}g",
    ])

    # Macros ajustados del día
    macros_adj = menu.get('macros_ajustados', {})
    if macros_adj:
        lines.extend([
            "",
            "MACROS AJUSTADOS (por deporte):",
            f"  Proteina: {macros_adj.get('proteina_g', 0)}g | Carbos: {macros_adj.get('carbos_g', 0)}g | Grasas: {macros_adj.get('grasas_g', 0)}g",
        ])

    return "\n".join(lines)


def format_suplementos(suplementos: list) -> str:
    """
    Formatea lista de suplementos para Telegram

    Args:
        suplementos: Lista de dicts de suplementos (de recomendar_suplementos())

    Returns:
        Texto formateado
    """
    if not suplementos:
        return "No se recomiendan suplementos adicionales por el momento."

    lines = [
        "--- TUS SUPLEMENTOS ---",
        "",
    ]

    for i, s in enumerate(suplementos, 1):
        lines.append(f"{i}. {s['nombre']}")
        lines.append(f"   Cantidad: {s['cantidad']}")
        lines.append(f"   Cuando: {s['timing']}")
        lines.append(f"   Por que: {s['razon']}")
        if s.get('nota'):
            lines.append(f"   Nota: {s['nota']}")
        lines.append("")

    return "\n".join(lines)


def format_plan_semanal(deportes: dict, plan: dict = None) -> str:
    """
    Formatea plan semanal para Telegram

    Args:
        deportes: Dict {dia: deporte}
        plan: Dict opcional con planes de menú por día

    Returns:
        Texto formateado
    """
    dias_orden = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']

    lines = [
        "--- TU SEMANA ---",
        "",
    ]

    for dia in dias_orden:
        deporte = deportes.get(dia, 'No definido')
        dia_display = dia.capitalize()
        lines.append(f"{dia_display}: {deporte}")

    return "\n".join(lines)


def format_revision(ajustes: dict) -> str:
    """
    Formatea resultado de revisión para Telegram

    Args:
        ajustes: Dict de calcular_ajuste_revision()

    Returns:
        Texto formateado
    """
    lines = [
        "--- REVISION DE PROGRESO ---",
        "",
        f"Peso anterior: {ajustes.get('peso_anterior', 'N/A')}kg",
        f"Peso actual: {ajustes.get('peso_actual', 'N/A')}kg",
        f"Cambio: {ajustes.get('delta_peso', 0):+.1f}kg",
        "",
        "Analisis:",
    ]

    for cambio in ajustes.get('cambios', []):
        lines.append(f"  - {cambio}")

    if ajustes.get('nuevos_macros'):
        nm = ajustes['nuevos_macros']
        lines.extend([
            "",
            "Nuevos macros recomendados:",
            f"  Calorias: {nm.get('calorias_objetivo', 'N/A')} kcal",
            f"  Proteina: {nm.get('proteina_g', 'N/A')}g",
            f"  Carbos: {nm.get('carbos_g', 'N/A')}g",
            f"  Grasas: {nm.get('grasas_g', 'N/A')}g",
        ])
    elif ajustes.get('mantener'):
        lines.extend([
            "",
            "Mantener macros actuales. No se necesitan cambios.",
        ])

    return "\n".join(lines)


def format_recetas(recetas: list, deporte: str = "") -> str:
    """
    Formatea lista de recetas para Telegram

    Args:
        recetas: Lista de recetas de buscar_recetas_por_deporte()
        deporte: Nombre del deporte (para el título)

    Returns:
        Texto formateado
    """
    titulo = f"--- RECETAS PARA {deporte.upper()} ---" if deporte else "--- RECETAS ---"

    lines = [titulo, ""]

    if not recetas:
        lines.append("No se encontraron recetas para este deporte.")
        return "\n".join(lines)

    for i, r in enumerate(recetas, 1):
        macros = r.get('macros_totales', {})
        lines.append(f"{i}. {r['nombre']}")
        lines.append(f"   {r.get('calorias_totales', 0)} kcal | P:{macros.get('proteina', 0)}g C:{macros.get('carbos', 0)}g G:{macros.get('grasas', 0)}g")
        lines.append(f"   Tiempo: {r.get('tiempo_preparacion', 'N/A')} | Dificultad: {r.get('dificultad', 'N/A')}")
        lines.append("")

    return "\n".join(lines)


def format_welcome() -> str:
    """Mensaje de bienvenida para nuevos usuarios"""
    return """Hola! Soy NutriBot, tu nutricionista deportivo personal.

Voy a ayudarte a crear un plan de alimentacion personalizado segun tus objetivos y deportes.

Para empezar, necesito conocerte un poco. Vamos a recopilar algunos datos basicos.

Para empezar, dime tu nombre?"""


def format_onboarding_complete(nombre: str, macros: dict) -> str:
    """Mensaje cuando se completa el onboarding"""
    return f"""Perfecto {nombre}! Ya tengo todo lo que necesito.

{format_macros(macros)}

Ahora necesito saber que deportes practicas cada dia de la semana para personalizar tu plan.

Dime, que deporte o actividad haras el lunes? (puedes decir "descanso" si no entrenas)"""


def format_weekly_complete(nombre: str, deportes: dict) -> str:
    """Mensaje cuando se completa el setup semanal"""
    lines = [
        f"Excelente {nombre}! Tu semana esta configurada:",
        "",
        format_plan_semanal(deportes),
        "",
        "Tu plan semanal de menus y suplementos esta listo!",
        "",
        "Puedes usar estos comandos:",
        "  /plan - Ver tu plan semanal",
        "  /recetas [deporte] - Buscar recetas",
        "  /suplementos - Ver suplementos recomendados",
        "  /revision - Hacer revision de progreso",
        "  /macros - Ver tus macros",
        "",
        "O simplemente preguntame lo que quieras sobre nutricion deportiva!",
    ]
    return "\n".join(lines)
