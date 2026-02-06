"""
Database Schema for Nutrition Bot

Define el schema de SQLite para el chatbot nutricionista.
Incluye tablas para usuarios, perfiles, historial, planes semanales y revisiones.
"""

USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    chat_id TEXT PRIMARY KEY,
    nombre TEXT,
    estado TEXT DEFAULT 'new_user',  -- 'new_user', 'onboarding', 'weekly_setup', 'active'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

USER_PROFILES_TABLE = """
CREATE TABLE IF NOT EXISTS user_profiles (
    chat_id TEXT PRIMARY KEY,
    peso_kg REAL,
    altura_cm REAL,
    edad INTEGER,
    sexo TEXT,  -- 'M', 'F'
    objetivo TEXT,  -- 'deficit', 'mantenimiento', 'superavit'
    porcentaje INTEGER,  -- -30, -20, -10, 0, +10, +15, +20
    factor_actividad REAL,  -- 1.2, 1.4, 1.6, 1.8, 2.0
    calorias_objetivo INTEGER,
    proteina_g INTEGER,
    carbos_g INTEGER,
    grasas_g INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chat_id) REFERENCES users(chat_id) ON DELETE CASCADE
);
"""

CONVERSATION_HISTORY_TABLE = """
CREATE TABLE IF NOT EXISTS conversation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id TEXT NOT NULL,
    role TEXT NOT NULL,  -- 'user', 'assistant'
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chat_id) REFERENCES users(chat_id) ON DELETE CASCADE
);
"""

WEEKLY_SCHEDULES_TABLE = """
CREATE TABLE IF NOT EXISTS weekly_schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id TEXT NOT NULL,
    semana_inicio DATE NOT NULL,
    deportes_json TEXT,  -- JSON: {"lunes": "gym", "miercoles": "running", ...}
    plan_json TEXT,  -- JSON: plan de menús completo
    suplementos_json TEXT,  -- JSON: lista de suplementos
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chat_id) REFERENCES users(chat_id) ON DELETE CASCADE
);
"""

USER_REVISIONS_TABLE = """
CREATE TABLE IF NOT EXISTS user_revisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id TEXT NOT NULL,
    peso_actual REAL NOT NULL,
    feedback TEXT,
    ajustes_json TEXT,  -- JSON: cambios recomendados
    fecha_revision TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chat_id) REFERENCES users(chat_id) ON DELETE CASCADE
);
"""

ONBOARDING_PROGRESS_TABLE = """
CREATE TABLE IF NOT EXISTS onboarding_progress (
    chat_id TEXT PRIMARY KEY,
    current_step TEXT,  -- 'nombre', 'peso', 'altura', 'edad', 'sexo', 'objetivo', 'porcentaje', 'actividad', 'deportes'
    data_json TEXT,  -- JSON con datos recopilados hasta ahora
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chat_id) REFERENCES users(chat_id) ON DELETE CASCADE
);
"""

# Índices para mejorar performance
INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_conversation_chat_id ON conversation_history(chat_id);",
    "CREATE INDEX IF NOT EXISTS idx_conversation_timestamp ON conversation_history(timestamp);",
    "CREATE INDEX IF NOT EXISTS idx_weekly_chat_id ON weekly_schedules(chat_id);",
    "CREATE INDEX IF NOT EXISTS idx_weekly_inicio ON weekly_schedules(semana_inicio);",
    "CREATE INDEX IF NOT EXISTS idx_revisions_chat_id ON user_revisions(chat_id);",
    "CREATE INDEX IF NOT EXISTS idx_revisions_fecha ON user_revisions(fecha_revision);"
]

ALL_TABLES = [
    USERS_TABLE,
    USER_PROFILES_TABLE,
    CONVERSATION_HISTORY_TABLE,
    WEEKLY_SCHEDULES_TABLE,
    USER_REVISIONS_TABLE,
    ONBOARDING_PROGRESS_TABLE
]
