#!/bin/bash

# Quick Local Testing Setup - No sudo required
# This creates all the files you need for local testing

echo "🏠 QUICK LOCAL TESTING SETUP"
echo "============================"

# Create local environment file
echo "📝 Creating .env.local template..."
cat > .env.local << 'EOF'
# Local Development Environment Configuration
# Copy this to .env and fill in your actual values

# Environment
ENVIRONMENT=development
DEBUG=true

# API Keys (REQUIRED - get these from your services)
OPENAI_API_KEY=your_openai_api_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Webhook Configuration (will be updated automatically by scripts)
WEBHOOK_URL=https://your-ngrok-url.ngrok-free.app
WEBHOOK_SECRET=local-development-secret-12345

# Database (SQLite for local development)
DATABASE_URL=sqlite:///./rudeai_bot_local.db

# Server Configuration
HOST=0.0.0.0
PORT=8000

# OpenAI Settings
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=40
OPENAI_TEMPERATURE=0.7

# Logging
LOG_LEVEL=DEBUG
LOG_FILE=
LOG_RETENTION=7 days

# Security & Rate Limiting (relaxed for local testing)
RATE_LIMIT_PER_MINUTE=60
MAX_MESSAGE_LENGTH=2000

# Monitoring
ENABLE_METRICS=true
METRICS_RETENTION_DAYS=1
EOF

# Create ngrok startup script
echo "🌐 Creating ngrok startup script..."
cat > start_ngrok.sh << 'EOF'
#!/bin/bash

echo "🌐 Starting ngrok tunnel for local bot testing..."

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo ""
    echo "❌ ngrok is not installed!"
    echo ""
    echo "📥 Install ngrok:"
    echo "   Option 1 - Direct download:"
    echo "   1. Go to https://ngrok.com/download"
    echo "   2. Download ngrok for macOS"
    echo "   3. Unzip and move to /usr/local/bin/:"
    echo "      unzip ngrok.zip"
    echo "      sudo mv ngrok /usr/local/bin/"
    echo ""
    echo "   Option 2 - Homebrew (if you have it):"
    echo "   brew install ngrok/ngrok/ngrok"
    echo ""
    echo "🔐 Then authenticate:"
    echo "   1. Sign up at https://dashboard.ngrok.com/signup"
    echo "   2. Get auth token from https://dashboard.ngrok.com/get-started/your-authtoken"
    echo "   3. Run: ngrok config add-authtoken YOUR_TOKEN"
    echo ""
    exit 1
fi

# Kill any existing ngrok processes
echo "🔄 Stopping any existing ngrok processes..."
pkill -f ngrok || true
sleep 2

# Start ngrok in background
echo "🚀 Starting ngrok tunnel on port 8000..."
ngrok http 8000 > /tmp/ngrok.log 2>&1 &
NGROK_PID=$!

# Wait for ngrok to start
echo "⏳ Waiting for ngrok to initialize..."
sleep 5

# Get the public URL
NGROK_URL=$(curl -s localhost:4040/api/tunnels 2>/dev/null | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    for tunnel in data['tunnels']:
        if tunnel['proto'] == 'https':
            print(tunnel['public_url'])
            break
except:
    print('')
" 2>/dev/null)

if [ -n "$NGROK_URL" ]; then
    echo ""
    echo "✅ ngrok tunnel is active!"
    echo "   Local URL:  http://localhost:8000"
    echo "   Public URL: $NGROK_URL"
    echo ""
    echo "🔗 Webhook URL for Telegram:"
    echo "   $NGROK_URL/webhook/local-development-secret-12345"
    echo ""
    echo "📊 ngrok dashboard: http://localhost:4040"
    echo ""

    # Update .env file if it exists
    if [ -f ".env" ]; then
        # Create backup
        cp .env .env.backup.$(date +%s)
        # Update WEBHOOK_URL
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s|WEBHOOK_URL=.*|WEBHOOK_URL=$NGROK_URL|" .env
        else
            sed -i "s|WEBHOOK_URL=.*|WEBHOOK_URL=$NGROK_URL|" .env
        fi
        echo "✅ Updated WEBHOOK_URL in .env file"
        echo ""
    fi

    echo "🛑 To stop ngrok: pkill -f ngrok"
    echo "📝 ngrok process ID: $NGROK_PID"

    # Keep script running to show status
    echo ""
    echo "✨ ngrok is running! Press Ctrl+C to stop this script (ngrok will keep running)"
    echo ""

    # Show real-time status
    trap 'echo ""; echo "🛑 Script stopped. ngrok is still running in background."; exit 0' INT

    while kill -0 $NGROK_PID 2>/dev/null; do
        sleep 10
    done

    echo "❌ ngrok process died unexpectedly"
else
    echo ""
    echo "❌ Failed to get ngrok URL"
    echo "   Troubleshooting:"
    echo "   1. Check if ngrok is authenticated: ngrok config check"
    echo "   2. Check ngrok status: curl localhost:4040/api/tunnels"
    echo "   3. Check ngrok logs: cat /tmp/ngrok.log"
    echo ""
    kill $NGROK_PID 2>/dev/null || true
fi
EOF

# Create bot startup script
echo "🤖 Creating bot startup script..."
cat > start_bot.sh << 'EOF'
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
EOF

# Create testing script
echo "🧪 Creating test script..."
cat > test_bot.sh << 'EOF'
#!/bin/bash

echo "🧪 TESTING LOCAL BOT"
echo "==================="
echo ""

# Check if bot is running
echo "🔍 Checking if bot is running..."
if ! curl -s --max-time 5 http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ Bot is not running on localhost:8000"
    echo ""
    echo "🚀 Start the bot:"
    echo "   1. In one terminal: ./start_ngrok.sh"
    echo "   2. In another terminal: ./start_bot.sh"
    echo ""
    exit 1
fi

echo "✅ Bot is running"
echo ""

# Test endpoints
echo "🔍 Testing bot endpoints:"
echo ""

echo "📍 /health endpoint:"
curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8000/health
echo ""

echo "📍 / (root) endpoint:"
curl -s http://localhost:8000/ | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8000/
echo ""

echo "📍 /ping endpoint:"
curl -s http://localhost:8000/ping | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8000/ping
echo ""

echo "📍 /status endpoint:"
curl -s http://localhost:8000/status | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8000/status
echo ""

# Check ngrok status
echo "🌐 Checking ngrok status:"
if curl -s --max-time 3 localhost:4040/api/tunnels > /dev/null 2>&1; then
    NGROK_INFO=$(curl -s localhost:4040/api/tunnels | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    for tunnel in data['tunnels']:
        print(f'   {tunnel[\"proto\"].upper()}: {tunnel[\"public_url\"]}')
except:
    print('   Unable to parse ngrok info')
" 2>/dev/null)

    if [ -n "$NGROK_INFO" ]; then
        echo "✅ ngrok is running:"
        echo "$NGROK_INFO"
    else
        echo "⚠️  ngrok API responded but couldn't parse tunnels"
    fi

    echo "   Dashboard: http://localhost:4040"
else
    echo "❌ ngrok is not running"
    echo "   Start it with: ./start_ngrok.sh"
fi

echo ""
echo "📱 TELEGRAM TESTING:"
echo "1. Make sure ngrok is running and shows HTTPS URL above"
echo "2. Message your bot on Telegram"
echo "3. Check the bot logs for incoming webhook requests"
echo "4. Monitor ngrok dashboard: http://localhost:4040"
echo ""

echo "🔧 TROUBLESHOOTING:"
echo "• Bot not responding: Check webhook URL is set correctly"
echo "• 'Service unavailable': Check API keys in .env file"
echo "• ngrok issues: Re-authenticate with your auth token"
echo "• Database errors: Delete rudeai_bot_local.db to reset"
echo ""
EOF

# Make scripts executable
chmod +x start_ngrok.sh start_bot.sh test_bot.sh

echo ""
echo "✅ Local testing environment created!"
echo ""
echo "📁 Files created:"
echo "   • .env.local          (Environment template)"
echo "   • start_ngrok.sh      (Start ngrok tunnel)"
echo "   • start_bot.sh        (Start bot server)"
echo "   • test_bot.sh         (Test all endpoints)"
echo ""
echo "🚀 QUICK START:"
echo "   1. Install ngrok: https://ngrok.com/download"
echo "   2. Setup environment: cp .env.local .env && edit .env"
echo "   3. Start tunnel: ./start_ngrok.sh"
echo "   4. Start bot: ./start_bot.sh (in new terminal)"
echo "   5. Test: ./test_bot.sh"
echo ""
echo "📖 For detailed instructions, see the generated scripts!"
echo ""