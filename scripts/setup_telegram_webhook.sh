#!/bin/bash

# Script para configurar el webhook de Telegram con ngrok

echo "=========================================="
echo " SETUP TELEGRAM WEBHOOK"
echo "=========================================="
echo ""

# Verificar que existe BOT_TOKEN
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo " Error: TELEGRAM_BOT_TOKEN no está configurado"
    echo ""
    echo "Configúralo en el archivo .env:"
    echo "  TELEGRAM_BOT_TOKEN=tu_token_aqui"
    echo ""
    exit 1
fi

# Pedir ngrok URL
echo "Ingresa tu ngrok URL (ejemplo: https://abc123.ngrok.io):"
read NGROK_URL

if [ -z "$NGROK_URL" ]; then
    echo " URL no puede estar vacía"
    exit 1
fi

# Quitar trailing slash si existe
NGROK_URL=${NGROK_URL%/}

WEBHOOK_URL="${NGROK_URL}/webhook"

echo ""
echo "Configurando webhook en Telegram..."
echo "URL: $WEBHOOK_URL"
echo ""

# Llamar a Telegram API
RESPONSE=$(curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
    -H "Content-Type: application/json" \
    -d "{\"url\": \"$WEBHOOK_URL\"}")

echo "Respuesta de Telegram:"
echo "$RESPONSE" | python3 -m json.tool

echo ""
echo " Webhook configurado!"
echo ""
echo "Ahora puedes enviar mensajes a tu bot en Telegram"
echo ""
