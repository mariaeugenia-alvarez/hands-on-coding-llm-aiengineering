"""
Script para inicializar la base de datos del chatbot nutricionista

Ejecutar: python scripts/init_db.py
"""

import sys
import os

# Agregar directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_setup import create_tables, DB_PATH


def main():
    """Inicializa la base de datos"""
    try:
        create_tables(DB_PATH)
        print(f"Ubicación: {DB_PATH}")

    except Exception as e:
        print(f" Error al inicializar base de datos")
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
