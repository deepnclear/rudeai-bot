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
