"""
Onboarding Handler - Gestiona el flujo de onboarding de nuevos usuarios

Flujo paso a paso:
1. nombre
2. peso_kg
3. altura_cm
4. edad
5. sexo
6. objetivo
7. porcentaje
8. factor_actividad
9. deportes_semana (transición a weekly_setup)

Cada paso valida la entrada y guarda progreso en onboarding_progress table.
"""

import os
import sys
import json
from typing import Optional, Dict, Tuple

# Agregar directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_setup import (
    get_db_connection,
    get_onboarding_progress,
    save_onboarding_progress,
    create_user,
    update_user_state,
    get_user
)
from utils.text_utils import (
    extract_number,
    extract_sexo,
    extract_objetivo,
    extract_factor_actividad,
    extract_porcentaje
)
from utils.formatters import format_onboarding_complete
from services.tools_service import calcular_macros_objetivo


# Orden de pasos del onboarding
ONBOARDING_STEPS = [
    'nombre',
    'peso_kg',
    'altura_cm',
    'edad',
    'sexo',
    'objetivo',
    'porcentaje',
    'factor_actividad'
]


class OnboardingHandler:
    """
    Handler para el flujo de onboarding de nuevos usuarios
    """

    def __init__(self, chat_id: str):
        """
        Inicializa el handler de onboarding

        Args:
            chat_id: ID del chat de Telegram
        """
        self.chat_id = str(chat_id)
        self.conn = get_db_connection()

    def __del__(self):
        """Cierra conexión al destruir el objeto"""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()

    def start_onboarding(self) -> str:
        """
        Inicia el proceso de onboarding

        Returns:
            Mensaje de bienvenida
        """
        # Verificar si ya existe el usuario
        user = get_user(self.chat_id, self.conn)

        if not user:
            # Crear usuario nuevo
            create_user(self.chat_id, estado='onboarding', conn=self.conn)

        # Inicializar progreso
        data = {}
        save_onboarding_progress(
            self.chat_id,
            current_step='nombre',
            data_json=json.dumps(data),
            conn=self.conn
        )

        return """Hola! Soy NutriBot, tu nutricionista deportivo personal.

Voy a ayudarte a crear un plan de alimentacion personalizado segun tus objetivos y deportes.

Para empezar, necesito conocerte un poco.

¿Cual es tu nombre?"""

    def process_step(self, user_message: str) -> Tuple[str, bool]:
        """
        Procesa un paso del onboarding

        Args:
            user_message: Mensaje del usuario

        Returns:
            Tupla (respuesta, onboarding_completado)
        """
        # Obtener progreso actual
        progress = get_onboarding_progress(self.chat_id, self.conn)

        if not progress:
            # No hay progreso, iniciar onboarding
            return self.start_onboarding(), False

        current_step = progress['current_step']
        data = json.loads(progress['data_json'])

        # Procesar según el paso actual
        if current_step == 'nombre':
            return self._process_nombre(user_message, data)

        elif current_step == 'peso_kg':
            return self._process_peso(user_message, data)

        elif current_step == 'altura_cm':
            return self._process_altura(user_message, data)

        elif current_step == 'edad':
            return self._process_edad(user_message, data)

        elif current_step == 'sexo':
            return self._process_sexo(user_message, data)

        elif current_step == 'objetivo':
            return self._process_objetivo(user_message, data)

        elif current_step == 'porcentaje':
            return self._process_porcentaje(user_message, data)

        elif current_step == 'factor_actividad':
            return self._process_factor_actividad(user_message, data)

        else:
            return "Error: Paso desconocido. Usa /start para reiniciar.", False

    def _process_nombre(self, text: str, data: dict) -> Tuple[str, bool]:
        """Procesa el nombre del usuario"""
        nombre = text.strip()

        if len(nombre) < 2:
            return "El nombre es muy corto. Por favor, dime tu nombre completo.", False

        data['nombre'] = nombre

        # Actualizar usuario con nombre
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE users SET nombre = ? WHERE chat_id = ?",
            (nombre, self.chat_id)
        )
        self.conn.commit()

        # Avanzar al siguiente paso
        self._save_and_advance(data, 'peso_kg')

        return f"Perfecto {nombre}! Ahora dime, cuanto pesas? (en kg)", False

    def _process_peso(self, text: str, data: dict) -> Tuple[str, bool]:
        """Procesa el peso del usuario"""
        peso = extract_number(text)

        if not peso or peso < 30 or peso > 250:
            return "Hmm, ese peso no parece correcto. Por favor, dime tu peso en kilogramos (ej: 75)", False

        data['peso_kg'] = peso

        self._save_and_advance(data, 'altura_cm')

        return f"Entendido, {peso}kg. Y tu altura? (en cm, ej: 175)", False

    def _process_altura(self, text: str, data: dict) -> Tuple[str, bool]:
        """Procesa la altura del usuario"""
        altura = extract_number(text)

        # Si el usuario puso metros (ej: 1.75), convertir a cm
        if altura and altura < 3:
            altura = altura * 100

        if not altura or altura < 100 or altura > 250:
            return "Esa altura no parece correcta. Dime tu altura en centimetros (ej: 175)", False

        data['altura_cm'] = int(altura)

        self._save_and_advance(data, 'edad')

        return f"{int(altura)}cm, perfecto! Ahora tu edad?", False

    def _process_edad(self, text: str, data: dict) -> Tuple[str, bool]:
        """Procesa la edad del usuario"""
        edad = extract_number(text)

        if not edad or edad < 15 or edad > 100:
            return "Esa edad no parece correcta. Por favor, dime tu edad en anos.", False

        data['edad'] = int(edad)

        self._save_and_advance(data, 'sexo')

        return f"{int(edad)} anos. Y tu sexo? (M/F)", False

    def _process_sexo(self, text: str, data: dict) -> Tuple[str, bool]:
        """Procesa el sexo del usuario"""
        sexo = extract_sexo(text)

        if not sexo:
            return "Por favor, responde M (masculino) o F (femenino)", False

        data['sexo'] = sexo

        self._save_and_advance(data, 'objetivo')

        return """Perfecto! Ahora dime tu objetivo principal:

- DEFICIT: Perder grasa corporal
- MANTENIMIENTO: Mantener peso actual
- SUPERAVIT: Ganar masa muscular

Cual es tu objetivo?""", False

    def _process_objetivo(self, text: str, data: dict) -> Tuple[str, bool]:
        """Procesa el objetivo del usuario"""
        objetivo = extract_objetivo(text)

        if not objetivo:
            return "No entendi tu objetivo. Responde: deficit, mantenimiento o superavit", False

        data['objetivo'] = objetivo

        self._save_and_advance(data, 'porcentaje')

        if objetivo == 'deficit':
            return """Objetivo: DEFICIT (perder grasa)

Que tan agresivo quieres el deficit?
- SUAVE: -10% (lento pero sostenible)
- MODERADO: -20% (equilibrado) [RECOMENDADO]
- AGRESIVO: -30% (rapido pero dificil)

Escribe el porcentaje (10, 20 o 30):""", False

        elif objetivo == 'superavit':
            return """Objetivo: SUPERAVIT (ganar musculo)

Que tan agresivo quieres el superavit?
- SUAVE: +10% (minima grasa)
- MODERADO: +15% (equilibrado) [RECOMENDADO]
- AGRESIVO: +20% (ganancia rapida)

Escribe el porcentaje (10, 15 o 20):""", False

        else:  # mantenimiento
            data['porcentaje'] = 0
            self._save_and_advance(data, 'factor_actividad')
            return """Objetivo: MANTENIMIENTO

Nivel de actividad fisica semanal:
- SEDENTARIO (1.2): Poco o ningun ejercicio
- LIGERA (1.4): Ejercicio ligero 1-2 dias/semana
- MODERADA (1.6): Ejercicio moderado 3-4 dias/semana [RECOMENDADO]
- ACTIVA (1.8): Ejercicio intenso 5-6 dias/semana
- MUY ACTIVA (2.0): Ejercicio muy intenso todos los dias

Escribe tu nivel (sedentario, ligera, moderada, activa, muy activa):""", False

    def _process_porcentaje(self, text: str, data: dict) -> Tuple[str, bool]:
        """Procesa el porcentaje de déficit/superávit"""
        porcentaje = extract_porcentaje(text)

        objetivo = data.get('objetivo')

        if objetivo == 'deficit':
            if not porcentaje or porcentaje not in [10, 20, 30]:
                return "Porcentaje no valido. Escribe 10, 20 o 30", False
        elif objetivo == 'superavit':
            if not porcentaje or porcentaje not in [10, 15, 20]:
                return "Porcentaje no valido. Escribe 10, 15 o 20", False

        data['porcentaje'] = porcentaje

        self._save_and_advance(data, 'factor_actividad')

        return f"""Perfecto, -{porcentaje}% deficit!

Ahora, nivel de actividad fisica semanal:
- SEDENTARIO (1.2): Poco o ningun ejercicio
- LIGERA (1.4): Ejercicio ligero 1-2 dias/semana
- MODERADA (1.6): Ejercicio moderado 3-4 dias/semana [RECOMENDADO]
- ACTIVA (1.8): Ejercicio intenso 5-6 dias/semana
- MUY ACTIVA (2.0): Ejercicio muy intenso todos los dias

Escribe tu nivel:""" if objetivo == 'deficit' else f"""Perfecto, +{porcentaje}% superavit!

Nivel de actividad fisica semanal:
- SEDENTARIO (1.2): Poco o ningun ejercicio
- LIGERA (1.4): Ejercicio ligero 1-2 dias/semana
- MODERADA (1.6): Ejercicio moderado 3-4 dias/semana [RECOMENDADO]
- ACTIVA (1.8): Ejercicio intenso 5-6 dias/semana
- MUY ACTIVA (2.0): Ejercicio muy intenso todos los dias

Escribe tu nivel:""", False

    def _process_factor_actividad(self, text: str, data: dict) -> Tuple[str, bool]:
        """Procesa el factor de actividad y completa el onboarding"""
        factor = extract_factor_actividad(text)

        if not factor:
            return "No entendi. Escribe: sedentario, ligera, moderada, activa o muy activa (o el numero 1.2-2.0)", False

        data['factor_actividad'] = factor

        # CALCULAR MACROS con tool
        macros = calcular_macros_objetivo(
            peso_kg=data['peso_kg'],
            objetivo=data['objetivo'],
            porcentaje=data.get('porcentaje', 0),
            factor_actividad=factor
        )

        # Guardar perfil completo en user_profiles
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO user_profiles
               (chat_id, peso_kg, altura_cm, edad, sexo, objetivo, porcentaje, factor_actividad,
                calorias_objetivo, proteina_g, carbos_g, grasas_g)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                self.chat_id,
                data['peso_kg'],
                data['altura_cm'],
                data['edad'],
                data['sexo'],
                data['objetivo'],
                data.get('porcentaje', 0),
                factor,
                macros['calorias_objetivo'],
                macros['proteina_g'],
                macros['carbos_g'],
                macros['grasas_g']
            )
        )
        self.conn.commit()

        # Cambiar estado a weekly_setup
        update_user_state(self.chat_id, 'weekly_setup', self.conn)

        # Limpiar progreso de onboarding (ya no se necesita)
        cursor.execute("DELETE FROM onboarding_progress WHERE chat_id = ?", (self.chat_id,))
        self.conn.commit()

        # Mensaje de finalización con macros
        response = format_onboarding_complete(data['nombre'], macros)

        return response, True  # True = onboarding completado

    def _save_and_advance(self, data: dict, next_step: str):
        """
        Guarda el progreso y avanza al siguiente paso

        Args:
            data: Datos recopilados
            next_step: Siguiente paso del onboarding
        """
        save_onboarding_progress(
            self.chat_id,
            current_step=next_step,
            data_json=json.dumps(data),
            conn=self.conn
        )


# ============================================================
# Test
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print(" Testing Onboarding Handler")
    print("=" * 60)

    # Simular flujo de onboarding
    test_chat_id = "test_onboarding_123"

    handler = OnboardingHandler(test_chat_id)

    # Paso 1: Start
    print("\n1. Start onboarding:")
    response, _ = handler.start_onboarding(), False
    print(f" {response[:100]}...")

    # Paso 2: Nombre
    print("\n2. Nombre: Juan")
    response, _ = handler.process_step("Juan")
    print(f" {response[:80]}...")

    # Paso 3: Peso
    print("\n3. Peso: 80")
    response, _ = handler.process_step("80")
    print(f" {response[:80]}...")

    # Paso 4: Altura
    print("\n4. Altura: 180")
    response, _ = handler.process_step("180")
    print(f" {response[:80]}...")

    # Paso 5: Edad
    print("\n5. Edad: 32")
    response, _ = handler.process_step("32")
    print(f" {response[:80]}...")

    # Paso 6: Sexo
    print("\n6. Sexo: M")
    response, _ = handler.process_step("M")
    print(f" {response[:100]}...")

    # Paso 7: Objetivo
    print("\n7. Objetivo: deficit")
    response, _ = handler.process_step("perder grasa")
    print(f" {response[:100]}...")

    # Paso 8: Porcentaje
    print("\n8. Porcentaje: 20")
    response, _ = handler.process_step("20")
    print(f" {response[:100]}...")

    # Paso 9: Factor actividad (completa onboarding)
    print("\n9. Factor actividad: moderada")
    response, completed = handler.process_step("moderada")
    print(f" Completed: {completed}")
    print(f" {response[:150]}...")

    # Verificar DB
    from database.db_setup import get_user_profile
    profile = get_user_profile(test_chat_id)
    if profile:
        print(f"\n Perfil creado:")
        print(f" Peso: {profile['peso_kg']}kg")
        print(f" Calorias: {profile['calorias_objetivo']} kcal")
        print(f" Macros: P:{profile['proteina_g']}g C:{profile['carbos_g']}g G:{profile['grasas_g']}g")

    # Cleanup
    conn = get_db_connection()
    conn.execute("DELETE FROM user_profiles WHERE chat_id = ?", (test_chat_id,))
    conn.execute("DELETE FROM users WHERE chat_id = ?", (test_chat_id,))
    conn.commit()
    conn.close()

    print("\n" + "=" * 60)
    print(" Test completado")
    print("=" * 60)
