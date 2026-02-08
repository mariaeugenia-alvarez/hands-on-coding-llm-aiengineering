# Telegram Nutrition Bot with RAG

Bot de Telegram que actúa como nutricionista deportivo usando RAG (Retrieval Augmented Generation). Proporciona asesoramiento nutricional personalizado, calcula macros, genera planes semanales y recomienda suplementos basándose en el perfil del usuario.

## Características

- **Onboarding completo**: Recopila datos del usuario (peso, altura, edad, objetivo, nivel de actividad)
- **Cálculo de macros**: Calcula calorías y macronutrientes personalizados según fórmulas científicas
- **RAG para consultas**: Responde preguntas usando base de conocimiento (990 chunks en FAISS)
- **Memoria persistente**: Guarda perfiles de usuario y conversaciones en SQLite
- **Planes semanales**: Genera menús y rutinas según deportes practicados
- **Recomendaciones de suplementos**: Sugiere suplementación personalizada con cálculos basados en peso/edad/objetivo

## Arquitectura

```
┌─────────────────────────────────────────────┐
│         TELEGRAM WEBHOOK (Flask)            │
│              app.py                         │
└──────────────────┬──────────────────────────┘
                   │
                   v
┌─────────────────────────────────────────────┐
│      MESSAGE ORCHESTRATOR                   │
│   handlers/message_orchestrator.py          │
│  • Clasifica intención del mensaje          │
│  • Enruta a: onboarding/conversación/tools  │
└───┬────────────┬─────────────┬──────────────┘
    │            │             │
    v            v             v
┌────────┐  ┌────────┐  ┌─────────────┐
│  RAG   │  │ TOOLS  │  │   DATABASE  │
│ FAISS  │  │System  │  │   SQLite    │
└────────┘  └────────┘  └─────────────┘
    │            │             │
    v            v             v
990 chunks   5 tools       6 tablas
embeddings   (macros,      (users, profiles,
HuggingFace  recetas,      history, schedules,
             menús,        revisions, onboarding)
             suplementos)
         ┌───────────────┐
         │ Claude Haiku  │
         │ (Anthropic)   │
         └───────────────┘
```

### Tecnologías

- **LLM**: Claude 3.5 Haiku (Anthropic API)
- **Vector Store**: FAISS con 990 chunks
- **Embeddings**: HuggingFace `sentence-transformers/all-MiniLM-L6-v2`
- **Database**: SQLite (6 tablas)
- **Framework**: LangChain para RAG
- **Web**: Flask para webhook de Telegram

## Estructura del Proyecto

```
/Users/maru/developement/hands-on-coding-llm-aiengineering/
│
├── app.py                          # Servidor Flask + webhook Telegram
├── requirements.txt                # Dependencias Python
├── .env                           # Variables de entorno (API keys)
├── README.md                      # Este archivo
│
├── config/
│   ├── settings.py                # Configuración centralizada
│   └── telegram.py                # Cliente API Telegram
│
├── database/
│   ├── models.py                  # Schema SQLite (6 tablas)
│   ├── db_setup.py                # Inicialización de base de datos
│   └── nutrition_bot.db           # Base de datos SQLite (generada)
│
├── services/
│   ├── rag_service.py             # Motor RAG (FAISS + búsqueda)
│   ├── tools_service.py           # 5 herramientas core (macros, recetas, etc.)
│   └── llm_service.py             # Wrapper de Claude Haiku
│
├── handlers/
│   ├── message_orchestrator.py    # Orquestador principal de mensajes
│   ├── onboarding_handler.py      # Flujo de onboarding (8 pasos)
│   └── commands_handler.py        # Comandos del bot (/start, /macros, etc.)
│
├── utils/
│   ├── text_utils.py              # Extracción de números, keywords
│   └── formatters.py              # Formateo de mensajes
│
├── data/
│   ├── alimentos.json             # Base de datos de alimentos
│   ├── recetas.json               # Recetas por deporte
│   ├── deportes_config.json       # Configuración de deportes
│   ├── knowledge_base/            # Documentos fuente para RAG
│   │   ├── guias/                 # Guías de nutrición (.md)
│   │   ├── web_sources/           # Contenido descargado de web (.md)
│   │   └── pdf_sources/           # PDFs convertidos a markdown
│   └── vectorstore_faiss/         # FAISS index (990 chunks)
│       ├── index.faiss
│       ├── index.pkl
│       └── metadata.json
│
└── scripts/
    ├── init_db.py                 # Inicializa base de datos
    ├── update_vectorstore.py      # Actualiza FAISS con nuevos documentos
    ├── fetch_web_content.py       # Descarga contenido web → markdown
    ├── process_pdfs.py            # Convierte PDFs → markdown
    └── setup_telegram_webhook.sh  # Helper para configurar webhook
```

## Base de Datos (SQLite)

### Tablas

1. **users**: Información básica y estado del usuario
2. **user_profiles**: Perfil nutricional (peso, macros, objetivo)
3. **conversation_history**: Historial de conversaciones
4. **weekly_schedules**: Planes semanales de menús y deportes
5. **user_revisions**: Seguimiento de progreso y ajustes
6. **onboarding_progress**: Estado temporal durante onboarding

## Instalación y Configuración

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

Crear archivo `.env` en la raíz del proyecto:

```bash
# API Keys
ANTHROPIC_API_KEY=tu_api_key_de_anthropic
TELEGRAM_BOT_TOKEN=tu_token_de_telegram

# Configuración
DEBUG=True
```

### 3. Inicializar base de datos

```bash
python scripts/init_db.py
```

Esto crea `data/nutrition_bot.db` con las 6 tablas necesarias.

### 4. Verificar vectorstore FAISS

El vectorstore ya está creado en `data/vectorstore_faiss/` con 990 chunks.

**Metadata del vectorstore**:
- **Modelo**: sentence-transformers/all-MiniLM-L6-v2
- **Chunks**: 990
- **Chunk size**: 1000 caracteres
- **Overlap**: 200 caracteres
- **Documentos**: Guías MD + 5 artículos web + 3 PDFs

Si necesitas actualizar el vectorstore:

```bash
python scripts/update_vectorstore.py
```

## Uso

### 1. Iniciar servidor Flask

```bash
python app.py
```

El servidor inicia en `http://localhost:5001`

### 2. Exponer con ngrok

En otra terminal:

```bash
ngrok http 5001
```

Copia la URL generada (ej: `https://abc123.ngrok-free.app`)

### 3. Configurar webhook de Telegram

**Opción A - Script automático** (recomendado):

```bash
export TELEGRAM_BOT_TOKEN="tu_token"
./scripts/setup_telegram_webhook.sh
# Ingresa tu URL de ngrok cuando se solicite
```

**Opción B - Manual**:

```bash
curl -X POST "https://api.telegram.org/bot<TU_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://abc123.ngrok-free.app/webhook"}'
```

### 4. Probar el bot

1. Abre Telegram
2. Busca tu bot
3. Envía `/start`
4. Sigue el proceso de onboarding

## Comandos del Bot

| Comando | Descripción |
|---------|-------------|
| `/start` | Inicia el bot y comienza onboarding |
| `/macros` | Recalcula macros (si cambió el peso) |
| `/plan` | Muestra plan semanal actual |
| `/recetas [deporte]` | Busca recetas para un deporte |
| `/suplementos` | Muestra suplementos recomendados |
| `/revision` | Realiza revisión de progreso semanal |
| `/help` | Muestra ayuda y comandos |

## Flujo de Onboarding

El bot guía al usuario a través de 8 pasos:

1. **Nombre**: ¿Cómo te llamas?
2. **Peso**: ¿Cuánto pesas? (kg)
3. **Altura**: ¿Cuánto mides? (cm)
4. **Edad**: ¿Cuántos años tienes?
5. **Sexo**: M/F
6. **Objetivo**: Déficit calórico / Mantenimiento / Superávit
7. **Porcentaje**: -30%, -20%, -10%, 0%, +10%, +15%, +20%
8. **Factor de actividad**: 1.2 (sedentario) a 2.0 (muy activo)

Al finalizar:
- Calcula calorías y macros personalizados
- Guarda perfil en base de datos
- Pasa a estado `active` para conversación normal

## RAG (Retrieval Augmented Generation)

El bot usa RAG para responder preguntas sobre nutrición:

### Proceso de búsqueda

```
Usuario: "¿Cuánta proteína necesito?"
    ↓
1. Embedding de la query (HuggingFace)
2. Búsqueda en FAISS (top 3 chunks)
3. Contexto augmentado:
   - RAG results (chunks relevantes)
   - User profile (peso, macros)
   - Conversation history (últimos 5)
    ↓
4. Prompt a Claude Haiku con contexto enriquecido
    ↓
5. Respuesta personalizada y fundamentada
```

### Base de Conocimiento

**Fuentes** (990 chunks total):
- Guías de nutrición deportiva (markdown)
- 5 artículos de Fitness Revolucionario
- 3 PDFs sobre nutrición y suplementación

**Para agregar nuevos documentos**:

1. Agregar archivos `.md` o `.pdf` a `data/knowledge_base/`
2. Ejecutar: `python scripts/update_vectorstore.py`

## Sistema de Tools

El bot tiene 5 herramientas especializadas:

### 1. `calcular_macros_objetivo`
Calcula calorías y macros según:
- Peso corporal
- Objetivo (déficit/mantenimiento/superávit)
- Factor de actividad

**Fórmula**:
```
Mantenimiento = peso × 22 × factor_actividad
Objetivo = mantenimiento × (1 ± porcentaje/100)
Proteína = peso × (2.0-2.5) g/kg
Grasas = peso × (0.5-1.5) g/kg
Carbos = (calorías - proteína*4 - grasas*9) / 4
```

### 2. `buscar_recetas_por_deporte`
Busca recetas ideales para un deporte específico en `data/recetas.json`

### 3. `generar_menu_diario`
Genera menú completo para un día:
- Desayuno (25%)
- Comida (40%)
- Cena (25%)
- Snacks (10%)

### 4. `recomendar_suplementos`
Recomienda suplementos con cálculos personalizados:
- Proteína Whey (0.3-0.4g/kg)
- Creatina (3-5g según edad)
- Omega-3 (dosis según edad/objetivo)
- Vitamina D (si +30 años)
- Cafeína pre-entreno (3-6mg/kg)

### 5. `calcular_ajuste_revision`
Calcula ajustes necesarios según progreso semanal:
- Compara peso actual vs anterior
- Analiza feedback del usuario
- Recomienda ajustes en macros

## Actualización del Vectorstore

### Agregar contenido web

1. Editar `scripts/fetch_web_content.py`:
```python
urls = [
    "https://ejemplo.com/articulo1",
    "https://ejemplo.com/articulo2",
]
```

2. Ejecutar:
```bash
python scripts/fetch_web_content.py
python scripts/update_vectorstore.py
```

### Agregar PDFs

1. Colocar PDFs en `data/knowledge_base/pdfs/`
2. Ejecutar:
```bash
python scripts/process_pdfs.py
python scripts/update_vectorstore.py
```

### Agregar guías markdown

1. Crear archivo `.md` en `data/knowledge_base/guias/`
2. Ejecutar:
```bash
python scripts/update_vectorstore.py
```

## Troubleshooting

### Error: "FAISS vectorstore not found"
```bash
python scripts/update_vectorstore.py
```

### Error: "Database not initialized"
```bash
python scripts/init_db.py
```

### Error: "ANTHROPIC_API_KEY not set"
Verificar que el archivo `.env` existe y contiene:
```
ANTHROPIC_API_KEY=tu_api_key
```

### Error: "Telegram webhook not responding"
1. Verificar que Flask está corriendo: `python app.py`
2. Verificar que ngrok está activo: `ngrok http 5001`
3. Verificar webhook configurado:
```bash
curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo
```

## Licencia

Proyecto académico - Práctica de RAG con LangChain y Anthropic Claude.
