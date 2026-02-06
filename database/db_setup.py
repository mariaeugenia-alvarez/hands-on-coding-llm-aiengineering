"""
Database Setup and Connection Management

Maneja la inicialización de la base de datos SQLite y la gestión de conexiones.
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional
from database.models import ALL_TABLES, INDEXES


# Path de la base de datos
DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "nutrition_bot.db",
)


def create_tables(db_path: str = DB_PATH) -> None:
    """
    Crea todas las tablas e índices en la base de datos

    Args:
        db_path: Ruta del archivo de base de datos
    """
    print(f"Creando base de datos en: {db_path}")

    # Asegurar que el directorio existe
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Crear todas las tablas
        for table_sql in ALL_TABLES:
            cursor.execute(table_sql)
            print(f"✓ Tabla creada")

        # Crear índices
        for index_sql in INDEXES:
            cursor.execute(index_sql)
            print(f"✓ Índice creado")

        conn.commit()
        print(f"\nBase de datos inicializada correctamente en {db_path}")

    except Exception as e:
        print(f"Error al crear tablas: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def get_db_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """
    Obtiene una conexión a la base de datos

    Args:
        db_path: Ruta del archivo de base de datos

    Returns:
        Conexión SQLite configurada
    """
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Para acceder a columnas por nombre
    return conn


def close_db_connection(conn: sqlite3.Connection) -> None:
    """
    Cierra una conexión a la base de datos

    Args:
        conn: Conexión a cerrar
    """
    if conn:
        conn.close()


# CRUD Operations Helper Functions


def get_user(chat_id: str, conn: Optional[sqlite3.Connection] = None) -> Optional[dict]:
    """
    Obtiene un usuario por chat_id

    Args:
        chat_id: ID del chat de Telegram
        conn: Conexión existente (opcional)

    Returns:
        Dict con datos del usuario o None si no existe
    """
    should_close = conn is None
    if conn is None:
        conn = get_db_connection()

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE chat_id = ?", (chat_id,))
        row = cursor.fetchone()

        if row:
            return dict(row)
        return None
    finally:
        if should_close:
            close_db_connection(conn)


def create_user(
    chat_id: str,
    nombre: str = "",
    estado: str = "onboarding",
    conn: Optional[sqlite3.Connection] = None,
) -> bool:
    """
    Crea un nuevo usuario

    Args:
        chat_id: ID del chat de Telegram
        nombre: Nombre del usuario
        estado: Estado inicial del usuario
        conn: Conexión existente (opcional)

    Returns:
        True si se creó correctamente
    """
    should_close = conn is None
    if conn is None:
        conn = get_db_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO users (chat_id, nombre, estado, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?)""",
            (chat_id, nombre, estado, datetime.now(), datetime.now()),
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al crear usuario: {e}")
        conn.rollback()
        return False
    finally:
        if should_close:
            close_db_connection(conn)


def update_user_state(
    chat_id: str, estado: str, conn: Optional[sqlite3.Connection] = None
) -> bool:
    """
    Actualiza el estado de un usuario

    Args:
        chat_id: ID del chat
        estado: Nuevo estado
        conn: Conexión existente (opcional)

    Returns:
        True si se actualizó correctamente
    """
    should_close = conn is None
    if conn is None:
        conn = get_db_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET estado = ?, updated_at = ? WHERE chat_id = ?",
            (estado, datetime.now(), chat_id),
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al actualizar estado: {e}")
        conn.rollback()
        return False
    finally:
        if should_close:
            close_db_connection(conn)


def get_user_profile(
    chat_id: str, conn: Optional[sqlite3.Connection] = None
) -> Optional[dict]:
    """
    Obtiene el perfil de un usuario

    Args:
        chat_id: ID del chat
        conn: Conexión existente (opcional)

    Returns:
        Dict con perfil del usuario o None
    """
    should_close = conn is None
    if conn is None:
        conn = get_db_connection()

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_profiles WHERE chat_id = ?", (chat_id,))
        row = cursor.fetchone()

        if row:
            return dict(row)
        return None
    finally:
        if should_close:
            close_db_connection(conn)


def save_conversation_message(
    chat_id: str, role: str, content: str, conn: Optional[sqlite3.Connection] = None
) -> bool:
    """
    Guarda un mensaje en el historial de conversación

    Args:
        chat_id: ID del chat
        role: 'user' o 'assistant'
        content: Contenido del mensaje
        conn: Conexión existente (opcional)

    Returns:
        True si se guardó correctamente
    """
    should_close = conn is None
    if conn is None:
        conn = get_db_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO conversation_history (chat_id, role, content, timestamp)
               VALUES (?, ?, ?, ?)""",
            (chat_id, role, content, datetime.now()),
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al guardar mensaje: {e}")
        conn.rollback()
        return False
    finally:
        if should_close:
            close_db_connection(conn)


def get_conversation_history(
    chat_id: str, limit: int = 10, conn: Optional[sqlite3.Connection] = None
) -> list:
    """
    Obtiene el historial de conversación de un usuario

    Args:
        chat_id: ID del chat
        limit: Número máximo de mensajes a obtener
        conn: Conexión existente (opcional)

    Returns:
        Lista de mensajes ordenados por timestamp DESC
    """
    should_close = conn is None
    if conn is None:
        conn = get_db_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT role, content, timestamp
               FROM conversation_history
               WHERE chat_id = ?
               ORDER BY timestamp DESC
               LIMIT ?""",
            (chat_id, limit),
        )
        rows = cursor.fetchall()

        # Invertir para que estén en orden cronológico
        messages = [dict(row) for row in rows]
        messages.reverse()

        return messages
    finally:
        if should_close:
            close_db_connection(conn)


def get_onboarding_progress(
    chat_id: str, conn: Optional[sqlite3.Connection] = None
) -> Optional[dict]:
    """
    Obtiene el progreso de onboarding de un usuario

    Args:
        chat_id: ID del chat
        conn: Conexión existente (opcional)

    Returns:
        Dict con progreso o None
    """
    should_close = conn is None
    if conn is None:
        conn = get_db_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM onboarding_progress WHERE chat_id = ?", (chat_id,)
        )
        row = cursor.fetchone()

        if row:
            return dict(row)
        return None
    finally:
        if should_close:
            close_db_connection(conn)


def save_onboarding_progress(
    chat_id: str,
    current_step: str,
    data_json: str,
    conn: Optional[sqlite3.Connection] = None,
) -> bool:
    """
    Guarda o actualiza el progreso de onboarding

    Args:
        chat_id: ID del chat
        current_step: Paso actual del onboarding
        data_json: JSON con datos recopilados
        conn: Conexión existente (opcional)

    Returns:
        True si se guardó correctamente
    """
    should_close = conn is None
    if conn is None:
        conn = get_db_connection()

    try:
        cursor = conn.cursor()

        # Check if existe
        cursor.execute(
            "SELECT chat_id FROM onboarding_progress WHERE chat_id = ?", (chat_id,)
        )
        exists = cursor.fetchone() is not None

        if exists:
            # Update
            cursor.execute(
                """UPDATE onboarding_progress
                   SET current_step = ?, data_json = ?, updated_at = ?
                   WHERE chat_id = ?""",
                (current_step, data_json, datetime.now(), chat_id),
            )
        else:
            # Insert
            cursor.execute(
                """INSERT INTO onboarding_progress (chat_id, current_step, data_json, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (chat_id, current_step, data_json, datetime.now(), datetime.now()),
            )

        conn.commit()
        return True
    except Exception as e:
        print(f"Error al guardar progreso onboarding: {e}")
        conn.rollback()
        return False
    finally:
        if should_close:
            close_db_connection(conn)
