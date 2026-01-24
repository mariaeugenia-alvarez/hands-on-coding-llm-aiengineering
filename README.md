# Telegram Bot Simple

Bot minimalista de Telegram con webhook.

## � Estructura

```
telegram-lambda-bot/
├── config/
│   └── settings.py       # Configuración (token)
├── api/
│   └── telegram.py       # Cliente Telegram (enviar mensajes)
├── handlers/
│   └── webhook.py        # Lógica de respuestas
└── app.py                # Servidor Flask
```

## 🚀 Uso

### 1. Instalar

```bash
pip install -r requirements.txt
```

### 2. Configurar token

```bash
export TELEGRAM_BOT_TOKEN="tu_token"
```

### 3. Ejecutar

```bash
python app.py
```

### 4. Exponer con ngrok

```bash
ngrok http 5000
```

### 5. Configurar webhook

```bash
curl -X POST https://api.telegram.org/bot<TOKEN>/setWebhook \
  -H "Content-Type: application/json" \
  -d '{"url": "https://tu-url.ngrok-free.app/webhook"}'
```

## ✏️ Personalizar

Edita `handlers/webhook.py` función `handle_webhook()` para cambiar las respuestas.
