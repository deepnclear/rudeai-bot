#!/bin/bash

echo "🤖 Starting RUDE.AI Bot locally..."
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo ""
    echo "🔧 Setup steps:"
    echo "   1. Copy template: cp .env.local .env"
    echo "   2. Edit .env and add your API keys:"
    echo "      - OPENAI_API_KEY (from https://platform.openai.com/api-keys)"
    echo "      - TELEGRAM_BOT_TOKEN (from @BotFather on Telegram)"
    echo ""
    exit 1
fi

# Check for required API keys
echo "🔍 Checking environment configuration..."

if ! grep -q "OPENAI_API_KEY=sk-" .env 2>/dev/null; then
    echo "❌ OPENAI_API_KEY not properly set in .env"
    echo "   Should start with: OPENAI_API_KEY=sk-"
    echo "   Get your key from: https://platform.openai.com/api-keys"
    exit 1
fi

if ! grep -q "TELEGRAM_BOT_TOKEN=.*:" .env 2>/dev/null; then
    echo "❌ TELEGRAM_BOT_TOKEN not properly set in .env"
    echo "   Should contain a colon: TELEGRAM_BOT_TOKEN=123456789:ABC..."
    echo "   Get your token from @BotFather on Telegram"
    exit 1
fi

echo "✅ API keys configured"

# Load environment variables
set -a
source .env
set +a

echo "✅ Environment loaded"
echo "   Environment: $ENVIRONMENT"
echo "   Debug: $DEBUG"
echo "   Port: $PORT"
echo "   Database: $DATABASE_URL"
echo "   Webhook: $WEBHOOK_URL"
echo ""

# Install dependencies if needed
if [ ! -d "venv" ] && [ ! -f ".venv/pyvenv.cfg" ]; then
    echo "📦 No virtual environment found. Install dependencies first:"
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    echo ""
fi

echo "🚀 Starting bot server..."
echo "   Access health check: http://localhost:$PORT/health"
echo "   Access root endpoint: http://localhost:$PORT/"
echo ""
echo "🔍 Bot logs will appear below:"
echo "============================================"

# Start the bot with auto-reload for development
python -m uvicorn rudeai_bot.webhook_server:app \
    --host 0.0.0.0 \
    --port $PORT \
    --reload \
    --log-level debug
