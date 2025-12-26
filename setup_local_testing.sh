#!/bin/bash

# Local Testing Setup Script for RUDE.AI Bot
# This script helps set up ngrok and local development environment

set -e

echo "🏠 LOCAL TESTING SETUP FOR RUDE.AI BOT"
echo "======================================"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install ngrok
install_ngrok() {
    echo ""
    echo "📥 INSTALLING NGROK"
    echo "==================="

    # Check if already installed
    if command_exists ngrok; then
        echo "✅ ngrok is already installed"
        ngrok version
        return 0
    fi

    echo "ngrok is not installed. Installing..."

    # Try different installation methods
    if command_exists brew; then
        echo "Installing via Homebrew..."
        brew install ngrok/ngrok/ngrok
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "Installing via direct download for macOS..."

        # Download ngrok for macOS
        curl -L https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-darwin-amd64.zip -o ngrok.zip
        unzip ngrok.zip
        chmod +x ngrok
        sudo mv ngrok /usr/local/bin/
        rm ngrok.zip

        echo "✅ ngrok installed to /usr/local/bin/ngrok"
    else
        echo "❌ Please install ngrok manually from https://ngrok.com/download"
        echo "   After installation, re-run this script"
        exit 1
    fi

    # Verify installation
    if command_exists ngrok; then
        echo "✅ ngrok installed successfully!"
        ngrok version
    else
        echo "❌ ngrok installation failed"
        exit 1
    fi
}

# Function to set up ngrok authentication
setup_ngrok_auth() {
    echo ""
    echo "🔐 NGROK AUTHENTICATION"
    echo "======================="

    echo "To use ngrok, you need a free account:"
    echo "1. Go to https://dashboard.ngrok.com/signup"
    echo "2. Sign up for a free account"
    echo "3. Copy your auth token from https://dashboard.ngrok.com/get-started/your-authtoken"
    echo ""

    read -p "Enter your ngrok auth token (or press Enter to skip): " auth_token

    if [ -n "$auth_token" ]; then
        ngrok config add-authtoken "$auth_token"
        echo "✅ Auth token configured"
    else
        echo "⚠️  Skipped auth token setup - you can add it later with: ngrok config add-authtoken YOUR_TOKEN"
    fi
}

# Function to create local environment file
create_local_env() {
    echo ""
    echo "📝 CREATING LOCAL ENVIRONMENT"
    echo "============================="

    if [ -f ".env.local" ]; then
        echo "⚠️  .env.local already exists. Backing up..."
        mv .env.local .env.local.backup.$(date +%s)
    fi

    cat > .env.local << 'EOF'
# Local Development Environment Configuration
# Copy this to .env and fill in your actual values

# Environment
ENVIRONMENT=development
DEBUG=true

# API Keys (REQUIRED - get these from your services)
OPENAI_API_KEY=your_openai_api_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Webhook Configuration (will be set automatically by ngrok script)
WEBHOOK_URL=http://localhost:8000
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

    echo "✅ Created .env.local with development configuration"
    echo ""
    echo "🔧 NEXT STEPS:"
    echo "1. Copy .env.local to .env: cp .env.local .env"
    echo "2. Edit .env and add your actual API keys:"
    echo "   - OPENAI_API_KEY (from https://platform.openai.com/api-keys)"
    echo "   - TELEGRAM_BOT_TOKEN (from @BotFather on Telegram)"
    echo ""
}

# Function to create local testing scripts
create_testing_scripts() {
    echo ""
    echo "📜 CREATING TESTING SCRIPTS"
    echo "=========================="

    # Create ngrok startup script
    cat > start_ngrok.sh << 'EOF'
#!/bin/bash

# Start ngrok tunnel for local bot testing

echo "🌐 Starting ngrok tunnel..."

# Kill any existing ngrok processes
pkill -f ngrok || true
sleep 2

# Start ngrok in background
ngrok http 8000 > /dev/null 2>&1 &
NGROK_PID=$!

# Wait for ngrok to start
sleep 3

# Get the public URL
NGROK_URL=$(curl -s localhost:4040/api/tunnels | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    for tunnel in data['tunnels']:
        if tunnel['proto'] == 'https':
            print(tunnel['public_url'])
            break
except:
    print('')
")

if [ -n "$NGROK_URL" ]; then
    echo "✅ ngrok tunnel active:"
    echo "   Local:  http://localhost:8000"
    echo "   Public: $NGROK_URL"
    echo ""
    echo "🔗 Webhook URL: $NGROK_URL/webhook/local-development-secret-12345"
    echo ""
    echo "💡 Update your .env file:"
    echo "   WEBHOOK_URL=$NGROK_URL"
    echo ""
    echo "🛑 To stop: pkill -f ngrok"
    echo "📊 ngrok dashboard: http://localhost:4040"

    # Automatically update .env if it exists
    if [ -f ".env" ]; then
        # Create backup
        cp .env .env.backup.$(date +%s)
        # Update WEBHOOK_URL
        sed -i.tmp "s|WEBHOOK_URL=.*|WEBHOOK_URL=$NGROK_URL|" .env
        rm .env.tmp
        echo "✅ Updated .env with ngrok URL"
    fi
else
    echo "❌ Failed to get ngrok URL"
    echo "   Check if ngrok is running: curl localhost:4040/api/tunnels"
    kill $NGROK_PID 2>/dev/null || true
fi
EOF

    # Create bot startup script
    cat > start_bot_local.sh << 'EOF'
#!/bin/bash

# Start the bot locally for testing

echo "🤖 Starting RUDE.AI Bot locally..."

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "   1. Copy template: cp .env.local .env"
    echo "   2. Edit .env and add your API keys"
    exit 1
fi

# Check for required variables
echo "🔍 Checking environment variables..."

if ! grep -q "OPENAI_API_KEY=sk-" .env; then
    echo "❌ OPENAI_API_KEY not set in .env"
    echo "   Get your key from: https://platform.openai.com/api-keys"
    exit 1
fi

if ! grep -q "TELEGRAM_BOT_TOKEN=.*:" .env; then
    echo "❌ TELEGRAM_BOT_TOKEN not set in .env"
    echo "   Get your token from @BotFather on Telegram"
    exit 1
fi

echo "✅ Environment variables look good"

# Load environment
set -a
source .env
set +a

echo "🚀 Starting bot server..."
echo "   Environment: $ENVIRONMENT"
echo "   Port: $PORT"
echo "   Database: $DATABASE_URL"
echo "   Webhook: $WEBHOOK_URL"
echo ""

# Start the bot
python -m uvicorn rudeai_bot.webhook_server:app --host 0.0.0.0 --port 8000 --reload --log-level debug
EOF

    # Create testing script
    cat > test_bot_local.sh << 'EOF'
#!/bin/bash

# Test the locally running bot

echo "🧪 TESTING LOCAL BOT"
echo "==================="

# Check if bot is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ Bot is not running on localhost:8000"
    echo "   Start it with: ./start_bot_local.sh"
    exit 1
fi

echo "✅ Bot is running locally"

# Test health endpoint
echo ""
echo "🔍 Testing /health endpoint:"
curl -s http://localhost:8000/health | python3 -m json.tool

# Test root endpoint
echo ""
echo "🔍 Testing / endpoint:"
curl -s http://localhost:8000/ | python3 -m json.tool

# Test ping endpoint
echo ""
echo "🔍 Testing /ping endpoint:"
curl -s http://localhost:8000/ping | python3 -m json.tool

# Show ngrok info if running
echo ""
if curl -s localhost:4040/api/tunnels > /dev/null 2>&1; then
    echo "🌐 ngrok tunnel info:"
    curl -s localhost:4040/api/tunnels | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    for tunnel in data['tunnels']:
        print(f'   {tunnel[\"proto\"].upper()}: {tunnel[\"public_url\"]}')
except:
    print('   Unable to parse ngrok info')
"
else
    echo "⚠️  ngrok not running - start with: ./start_ngrok.sh"
fi

echo ""
echo "📱 To test with Telegram:"
echo "1. Make sure ngrok is running (./start_ngrok.sh)"
echo "2. Update your bot's webhook URL via @BotFather or the webhook endpoint"
echo "3. Send a message to your bot on Telegram"
echo ""
EOF

    chmod +x start_ngrok.sh start_bot_local.sh test_bot_local.sh

    echo "✅ Created testing scripts:"
    echo "   - start_ngrok.sh     (Start ngrok tunnel)"
    echo "   - start_bot_local.sh (Start bot locally)"
    echo "   - test_bot_local.sh  (Test bot endpoints)"
    echo ""
}

# Function to show usage instructions
show_usage() {
    echo ""
    echo "🎯 LOCAL TESTING WORKFLOW"
    echo "========================="
    echo ""
    echo "1. 🔧 SETUP (one-time):"
    echo "   • Set up API keys in .env file"
    echo "   • Configure ngrok authentication"
    echo ""
    echo "2. 🚀 START TESTING:"
    echo "   Terminal 1: ./start_ngrok.sh     # Start public tunnel"
    echo "   Terminal 2: ./start_bot_local.sh # Start bot server"
    echo "   Terminal 3: ./test_bot_local.sh  # Test endpoints"
    echo ""
    echo "3. 📱 TEST ON TELEGRAM:"
    echo "   • Send messages to your bot"
    echo "   • Check logs in Terminal 2"
    echo "   • Monitor requests at http://localhost:4040"
    echo ""
    echo "4. 🛑 STOP:"
    echo "   • Ctrl+C in both terminals"
    echo "   • pkill -f ngrok"
    echo ""
    echo "📚 Quick Commands:"
    echo "   ./setup_local_testing.sh install  # Install ngrok"
    echo "   ./setup_local_testing.sh env      # Create .env template"
    echo "   ./setup_local_testing.sh scripts  # Create testing scripts"
    echo "   ./setup_local_testing.sh help     # Show this help"
    echo ""
}

# Main script logic
case "${1:-setup}" in
    "install")
        install_ngrok
        setup_ngrok_auth
        ;;
    "env")
        create_local_env
        ;;
    "scripts")
        create_testing_scripts
        ;;
    "setup")
        install_ngrok
        setup_ngrok_auth
        create_local_env
        create_testing_scripts
        show_usage
        ;;
    "help")
        show_usage
        ;;
    *)
        echo "❌ Unknown command: $1"
        show_usage
        exit 1
        ;;
esac

echo ""
echo "🎉 Setup complete! Ready for local testing."
echo "   Run './setup_local_testing.sh help' for usage instructions."