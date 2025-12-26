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
