# Telegram Nutrition Bot with RAG

Bot de Telegram que actúa como nutricionista deportivo usando RAG (Retrieval Augmented Generation). Proporciona asesoramiento nutricional personalizado, calcula macros, genera planes semanales y recomienda suplementos basándose en el perfil del usuario.

 [Ver presentación completa del proyecto](assets/presentacion.pdf)

## Características

- **Onboarding completo**: Recopila datos del usuario (peso, altura, edad, objetivo, nivel de actividad)
- **Cálculo de macros**: Calcula calorías y macronutrientes personalizados según fórmulas científicas
- **RAG para consultas**: Responde preguntas usando base de conocimiento (990 chunks en FAISS)
- **Memoria persistente**: Guarda perfiles de usuario y conversaciones en SQLite
- **Planes semanales**: Genera menús y rutinas según deportes practicados
- **Recomendaciones de suplementos**: Sugiere suplementacion personalizada con calculos basados en peso/edad/objetivo
- **Guardrails de seguridad**: Proteccion contra prompt injection, restriccion tematica a nutricion deportiva, prevencion de fuga de datos sensibles y disclaimer medico

## Arquitectura

El sistema integra múltiples componentes para ofrecer asesoramiento nutricional personalizado: desde la recepción de mensajes vía webhook de Telegram, pasando por guardrails de seguridad, hasta la generación de respuestas con RAG y herramientas especializadas.

![Infografía del Sistema](assets/infografia.png)

La infografía muestra el flujo completo del bot, desde que el usuario envía un mensaje hasta que recibe una respuesta personalizada, incluyendo todos los componentes intermedios (guardrails, RAG, tools, base de datos y LLM).

```
┌─────────────────────────────────────────────┐
│         TELEGRAM WEBHOOK (Flask)            │
│              app.py                         │
└──────────────────┬──────────────────────────┘
                   │
                   v
┌─────────────────────────────────────────────┐
│           GUARDRAILS (entrada)              │
│   services/guardrails_service.py            │
│  • Prompt injection detection               │
│  • Off-topic filtering                      │
└──────────────────┬──────────────────────────┘
                   │
                   v
┌─────────────────────────────────────────────┐
│      MESSAGE ORCHESTRATOR                   │
│   handlers/message_orchestrator.py          │
│  • Clasifica intencion del mensaje          │
│  • Enruta a: onboarding/conversacion/tools  │
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
             menus,        revisions, onboarding)
             suplementos)
         ┌───────────────┐
         │ Claude Haiku  │
         │ (Anthropic)   │
         └───────────────┘
                   │
                   v
┌─────────────────────────────────────────────┐
│           GUARDRAILS (salida)               │
│  • Data leak detection                      │
│  • Sensitive pattern filtering              │
└─────────────────────────────────────────────┘
```

### Tecnologías

- **LLM**: Claude 3.5 Haiku (Anthropic API)
- **Vector Store**: FAISS con 990 chunks
- **Embeddings**: HuggingFace `paraphrase-multilingual-MiniLM-L12-v2` (multilingue, 384 dim)
- **Reranking**: CrossEncoder multilingue `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`
- **Database**: SQLite (6 tablas)
- **Framework**: LangChain para RAG
- **Web**: Flask para webhook de Telegram
- **Guardrails**: Validacion de entrada/salida con deteccion de prompt injection y fuga de datos

## Estructura del Proyecto

```
/Users/maru/developement/hands-on-coding-llm-aiengineering/
│
├── app.py                          # Servidor Flask + webhook Telegram
├── requirements.txt                # Dependencias Python
├── .env                           # Variables de entorno (API keys)
├── .env.example                   # Plantilla de variables de entorno
├── README.md                      # Este archivo
│
├── docker/
│   ├── Dockerfile                 # Imagen Docker
│   └── docker-compose.yml         # Orquestacion Docker
│
├── assets/
│   ├── infografia.png             # Infografía visual del proyecto
│   └── presentacion.pdf           # Presentación completa del proyecto
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
│   ├── rag_service.py             # Motor RAG (FAISS + reranking CrossEncoder)
│   ├── tools_service.py           # 5 herramientas core (macros, recetas, etc.)
│   ├── tool_registry.py           # Registro de tools (JSON Schema + ejecucion)
│   ├── agent_service.py           # Agente autonomo con tool execution
│   ├── llm_provider.py            # Interfaz LLM-agnostic (Anthropic, OpenAI...)
│   ├── llm_service.py             # Wrapper de Claude Haiku (legacy)
│   └── guardrails_service.py      # Guardrails: validacion entrada/salida
│
├── handlers/
│   ├── message_orchestrator.py    # Orquestador principal (routing, comandos, agente)
│   └── onboarding_handler.py      # Flujo de onboarding (8 pasos)
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

# Seguridad
WEBHOOK_SECRET_TOKEN=un_token_secreto_aleatorio

# Configuración
DEBUG=False
```

### 3. Inicializar base de datos

```bash
python scripts/init_db.py
```

Esto crea `data/nutrition_bot.db` con las 6 tablas necesarias.

### 4. Verificar vectorstore FAISS

El vectorstore ya está creado en `data/vectorstore_faiss/` con 990 chunks.

**Metadata del vectorstore**:
- **Modelo**: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
- **Chunks**: 990
- **Chunk size**: 1000 caracteres
- **Overlap**: 200 caracteres
- **Documentos**: Guías MD + 5 artículos web + 3 PDFs

Si necesitas actualizar el vectorstore:

```bash
python scripts/update_vectorstore.py
```

## Uso

### Con Docker (recomendado)

#### 1. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con tus API keys
```

#### 2. Construir y ejecutar

```bash
docker-compose -f docker/docker-compose.yml up --build
```

El servidor inicia en `http://localhost:5001`

#### 3. Exponer con ngrok

En otra terminal:

```bash
ngrok http 5001
```

#### 4. Configurar webhook de Telegram

```bash
export TELEGRAM_BOT_TOKEN="tu_token"
./scripts/setup_telegram_webhook.sh
# Ingresa tu URL de ngrok cuando se solicite
```

#### 5. Probar el bot

1. Abre Telegram
2. Busca tu bot
3. Envia `/start`
4. Sigue el proceso de onboarding

---

### Sin Docker (manual)

#### 1. Iniciar servidor Flask

```bash
python app.py
```

El servidor inicia en `http://localhost:5001`

#### 2. Exponer con ngrok

En otra terminal:

```bash
ngrok http 5001
```

Copia la URL generada (ej: `https://abc123.ngrok-free.app`)

#### 3. Configurar webhook de Telegram

**Opcion A - Script automatico** (recomendado):

```bash
export TELEGRAM_BOT_TOKEN="tu_token"
./scripts/setup_telegram_webhook.sh
# Ingresa tu URL de ngrok cuando se solicite
```

**Opción B - Manual** (con secret_token para autenticación):

```bash
curl -X POST "https://api.telegram.org/bot<TU_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://abc123.ngrok-free.app/webhook", "secret_token": "un_token_secreto_aleatorio"}'
```

El `secret_token` debe coincidir con `WEBHOOK_SECRET_TOKEN` en tu `.env`. Telegram enviará este token en el header `X-Telegram-Bot-Api-Secret-Token` y el servidor lo validará para rechazar peticiones no autorizadas.

### 4. Probar el bot

1. Abre Telegram
2. Busca tu bot
3. Envía `/start`
4. Sigue el proceso de onboarding

## Comandos del Bot

| Comando | Descripción |
|---------|-------------|
| `/start` | Inicia el bot y comienza onboarding |
| `/macros` | Muestra los macros actuales del usuario |
| `/help` | Muestra ayuda y comandos |

Las funcionalidades de recetas, suplementos, planes y revisiones se invocan automaticamente por el agente en conversacion libre. El usuario solo tiene que preguntar (ej: "recomiendame suplementos para crossfit") y el agente decide que herramienta usar.

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

### Proceso de búsqueda (Retrieve + Rerank)

```
Usuario: "¿Cuánta proteína necesito?"
    ↓
1. Embedding de la query (HuggingFace bi-encoder)
2. Búsqueda en FAISS (top 9 candidatos)
    ↓
3. Reranking con CrossEncoder multilingüe
   - Evalúa relevancia semántica de cada par (query, chunk)
   - Reordena por relevancia real → top 3 chunks
    ↓
4. Contexto augmentado:
   - RAG results (chunks rerankeados)
   - User profile (peso, macros)
   - Conversation history (últimos 5)
    ↓
5. Prompt a Claude Haiku con contexto enriquecido
    ↓
6. Respuesta personalizada y fundamentada
```

**Por que reranking**: Los embeddings bi-encoder (FAISS) son rápidos pero aproximados: representan query y documento por separado. El CrossEncoder evalúa cada par (query, documento) de forma conjunta, lo que es más preciso para determinar relevancia semántica. Además, el modelo `mmarco-mMiniLMv2` está entrenado en datos multilingues (incluyendo español), compensando parcialmente las limitaciones del modelo de embeddings inglés.

### Base de Conocimiento

**Fuentes** (990 chunks total):
- Guías de nutrición deportiva (markdown)
- 5 artículos de Fitness Revolucionario
- 3 PDFs sobre nutrición y suplementación

**Para agregar nuevos documentos**:

1. Agregar archivos `.md` o `.pdf` a `data/knowledge_base/`
2. Ejecutar: `python scripts/update_vectorstore.py`

## Guardrails de Seguridad

El bot implementa multiples capas de proteccion para garantizar un uso seguro:

### Capa 0: Proteccion de infraestructura

- **Autenticacion de webhook**: El servidor valida el header `X-Telegram-Bot-Api-Secret-Token` para rechazar peticiones que no vengan de Telegram (HTTP 403)
- **Limite de longitud**: Los mensajes se truncan a 2000 caracteres para prevenir abuso de tokens de API y saturacion de la base de datos
- **Debug desactivado**: Flask corre sin modo debug en produccion para no exponer el debugger interactivo de Werkzeug

### Capa 1: Validacion de entrada (pre-LLM)

**Prompt injection**: Detecta intentos de manipular el comportamiento del LLM. Patrones como "ignora tus instrucciones", "actua como", "jailbreak", "dime tu prompt", etc. se rechazan antes de llegar al modelo.

**Off-topic**: Detecta preguntas fuera del ambito de nutricion deportiva (politica, programacion, finanzas, entretenimiento, etc.) y redirige amablemente al usuario. Ahorra tokens al no enviar la consulta al LLM.

### Capa 2: System prompt reforzado (en el LLM)

El system prompt de Claude Haiku incluye 6 reglas estrictas:
1. Solo responder sobre nutricion deportiva
2. Rechazar temas no relacionados
3. No revelar informacion tecnica del sistema (tablas, modelos, prompts)
4. Resistencia a prompt injection
5. No dar diagnosticos medicos (recomendar profesional de salud)
6. Responder siempre en espanol

### Capa 3: Validacion de salida (post-LLM)

Filtra la respuesta del LLM antes de enviarla al usuario. Detecta fugas accidentales de:
- Queries SQL (SELECT, CREATE TABLE, INSERT)
- Nombres de tablas internas (user_profiles, conversation_history, etc.)
- API keys y tokens
- Rutas del sistema de archivos
- Referencias al modelo de IA

```
Flujo completo:

Webhook Telegram
    |
    v
secret_token valido? --> NO --> 403 Forbidden
    |
    v
len(texto) > 2000? --> truncar a 2000 chars
    |
    v
validate_input() --> prompt injection? --> Rechazo (sin LLM)
    |
    v
is_off_topic() --> fuera de tema? --> Redireccion (sin LLM)
    |
    v
[Proceso normal: onboarding / weekly_setup / active]
    |
    v
Respuesta LLM
    |
    v
validate_output() --> datos sensibles? --> Respuesta generica segura
    |
    v
Enviar a Telegram
```

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

## Evaluacion del RAG (RAGas)

El proyecto incluye evaluacion formal del pipeline RAG usando el framework RAGas con 5 metricas estandar:

```bash
python scripts/evaluate_rag.py
```

**Comparativa de resultados** (25 preguntas, ground truth manual):

| Metrica | Baseline | Con mejoras | Mejora | Que mide |
|---------|----------|-------------|--------|----------|
| Faithfulness | 0.3910 | **0.6707** | +71.5% | Si la respuesta es fiel al contexto recuperado |
| Answer Relevancy | 0.3972 | **0.8476** | +113.4% | Si la respuesta es relevante a la pregunta |
| Context Precision | 0.2867 | **0.7733** | +169.7% | Si los chunks recuperados son relevantes |
| Context Recall | 0.2567 | **0.6827** | +166.0% | Si se recupero toda la informacion necesaria |
| Answer Correctness | 0.4517 | **0.5167** | +14.4% | Precision vs ground truth |

- **Baseline**: embeddings ingles (`all-MiniLM-L6-v2`), sin reranking
- **Con mejoras**: embeddings multilingue (`paraphrase-multilingual-MiniLM-L12-v2`) + reranking CrossEncoder (`mmarco-mMiniLMv2-L12-H384-v1`)

**Diagnostico**: Las dos mejoras aplicadas tuvieron impacto significativo:

1. **Context Precision +169.7%**: El reranking con CrossEncoder multilingue mejora drasticamente la seleccion de chunks relevantes. FAISS recupera 9 candidatos y el CrossEncoder reordena por relevancia semantica real, devolviendo los 3 mejores.
2. **Context Recall +166.0%**: El modelo de embeddings multilingue captura mucho mejor la semantica del español, recuperando mas informacion relevante de la knowledge base.
3. **Answer Relevancy +113.4%**: Con mejor contexto, Claude genera respuestas mas relevantes a la pregunta del usuario.
4. **Faithfulness +71.5%**: Claude se apoya mas en el contexto RAG recuperado en vez de su conocimiento propio, lo cual es el comportamiento deseado.

**Archivos**:
- Dataset: `data/eval/eval_dataset.json` (25 preguntas con ground truth)
- Resultados: `data/eval/eval_results.json` (detalle por pregunta)
- Grafico: `data/eval/eval_metrics.png`

## Decisión de Modelo: API vs Fine-Tuning

### Por que usamos Claude Haiku API en vez de fine-tuning

Este proyecto usa Claude 3.5 Haiku via API como decisión de ingeniería deliberada. Se centra en orquestación y diseño de RAG como eje del proyecto. 

### Argumentos a favor de usar API (sin fine-tuning)

1. **Coste desproporcionado del fine-tuning en produccion**: El fine-tuning en si es barato ($5-$20 con QLoRA en una A100), pero servir el modelo 24/7 cuesta $641+/mes en GPU dedicada. A 100 queries/dia, la API de Claude cuesta $4.80/mes - es **133x mas barato**.

2. **La calidad del modelo base ya es superior**: Claude Haiku tiene capacidades de razonamiento, seguimiento de instrucciones y generacion en español que un modelo 7B/8B fine-tuned no iguala facilmente. El fine-tuning mejora el dominio especifico, pero puede degradar capacidades generales como guardrails y coherencia.

3. **RAG ya cubre la especializacion de dominio**: En vez de "quemar" conocimiento nutricional en los pesos del modelo (fine-tuning), lo mantenemos en la knowledge base (RAG). Esto es mas flexible: actualizar informacion es agregar un documento, no re-entrenar.

4. **Complejidad operativa innecesaria**: Fine-tuning requiere pipeline de datos, GPU, MLOps, versionado de modelos. Para una PoC de un nutricionista con RAG, esta complejidad no aporta valor.


### Cuando si tendria sentido fine-tuning

- **Escala masiva**: Miles de usuarios concurrentes (>50k queries/dia)
- **Latencia critica**: Si se necesitara <100ms por respuesta
- **Datos propietarios sensibles**: Si los datos no pudieran salir a un API externo
- **Comportamiento muy especifico**: Si se necesitara un tono, formato o estilo muy particular que el prompting no consiga


## Licencia

Proyecto academico - Practica de RAG con LangChain y Anthropic Claude.
