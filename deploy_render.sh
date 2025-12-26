#!/bin/bash

# Render deployment helper script for RUDE.AI bot
# This script helps with Render deployment setup and troubleshooting

set -e

echo "🎨 RENDER DEPLOYMENT HELPER"
echo "============================"

# Check if we're in the right directory
if [ ! -f "render.yaml" ]; then
    echo "❌ Error: render.yaml not found. Run this script from the project root."
    exit 1
fi

# Function to show help
show_help() {
    echo ""
    echo "🤖 RUDE.AI RENDER DEPLOYMENT"
    echo "=============================="
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  setup       Show setup instructions for Render"
    echo "  env         Show environment variables to set"
    echo "  check       Run diagnostics"
    echo "  webhook     Generate webhook secret"
    echo "  help        Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 setup         # Show deployment steps"
    echo "  $0 env           # Show required environment variables"
    echo "  $0 check         # Check bot status"
    echo ""
}

# Function to show setup instructions
show_setup() {
    echo ""
    echo "🎨 RENDER DEPLOYMENT SETUP"
    echo "=========================="
    echo ""
    echo "1. 📁 CONNECT REPOSITORY:"
    echo "   • Go to https://render.com"
    echo "   • Click 'New' → 'Web Service'"
    echo "   • Connect your GitHub repository"
    echo "   • Select this repository: rudeai-bot"
    echo ""
    echo "2. ⚙️  SERVICE CONFIGURATION:"
    echo "   • Name: rudeai-bot"
    echo "   • Runtime: Python 3"
    echo "   • Build Command: pip install -r requirements.txt"
    echo "   • Start Command: python -m uvicorn rudeai_bot.webhook_server:app --host 0.0.0.0 --port \$PORT"
    echo "   • Plan: Free (sufficient for Telegram bots)"
    echo ""
    echo "3. 🗄️ DATABASE SETUP:"
    echo "   • Go to Render dashboard"
    echo "   • Click 'New' → 'PostgreSQL'"
    echo "   • Name: rudeai-bot-db"
    echo "   • Plan: Free (90 days)"
    echo "   • Copy the DATABASE_URL after creation"
    echo ""
    echo "4. 📋 ENVIRONMENT VARIABLES:"
    echo "   Run '$0 env' to see required variables"
    echo ""
    echo "5. 🚀 DEPLOY:"
    echo "   • Click 'Create Web Service'"
    echo "   • Render will automatically deploy from your GitHub repo"
    echo "   • Monitor logs for any issues"
    echo ""
    echo "6. 🔗 WEBHOOK SETUP:"
    echo "   • After deployment, copy your Render URL"
    echo "   • Set WEBHOOK_URL environment variable"
    echo "   • Restart the service"
    echo ""
}

# Function to show environment variables
show_env() {
    echo ""
    echo "🔧 REQUIRED ENVIRONMENT VARIABLES"
    echo "================================="
    echo ""
    echo "Set these in Render Dashboard → Environment:"
    echo ""

    # Generate webhook secret if not exists
    webhook_secret=$(openssl rand -hex 32 2>/dev/null || echo "$(date +%s | sha256sum | cut -d' ' -f1)")

    echo "🔐 SECRETS (mark as secret in Render):"
    echo "   OPENAI_API_KEY=your_openai_api_key_here"
    echo "   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here"
    echo "   WEBHOOK_SECRET=$webhook_secret"
    echo ""
    echo "🔗 URLs:"
    echo "   WEBHOOK_URL=https://your-app-name.onrender.com"
    echo "   DATABASE_URL=postgresql://user:pass@host:port/db (from Render PostgreSQL)"
    echo ""
    echo "⚙️  CONFIGURATION:"
    echo "   ENVIRONMENT=production"
    echo "   DEBUG=false"
    echo "   HOST=0.0.0.0"
    echo "   OPENAI_MODEL=gpt-4o-mini"
    echo "   OPENAI_MAX_TOKENS=40"
    echo "   OPENAI_TEMPERATURE=0.7"
    echo "   RATE_LIMIT_PER_MINUTE=20"
    echo "   MAX_MESSAGE_LENGTH=1000"
    echo "   LOG_LEVEL=INFO"
    echo "   ENABLE_METRICS=true"
    echo "   METRICS_RETENTION_DAYS=7"
    echo ""
    echo "💡 TIPS:"
    echo "   • Mark sensitive variables as 'secret' in Render"
    echo "   • DATABASE_URL is auto-generated when you create PostgreSQL service"
    echo "   • WEBHOOK_URL should match your Render service URL"
    echo ""
}

# Function to generate webhook secret
generate_webhook() {
    echo ""
    echo "🔐 WEBHOOK SECRET GENERATOR"
    echo "=========================="
    echo ""

    if command -v openssl &> /dev/null; then
        webhook_secret=$(openssl rand -hex 32)
        echo "Generated webhook secret:"
        echo "WEBHOOK_SECRET=$webhook_secret"
    else
        webhook_secret=$(date +%s | sha256sum | cut -d' ' -f1 2>/dev/null || echo "fallback-secret-$(date +%s)")
        echo "Generated webhook secret (install openssl for better security):"
        echo "WEBHOOK_SECRET=$webhook_secret"
    fi

    echo ""
    echo "💾 Save this secret and add it to your Render environment variables!"
    echo ""
}

# Function to run diagnostics
run_diagnostics() {
    echo ""
    echo "🔍 RUNNING DIAGNOSTICS"
    echo "====================="

    echo "📊 Checking application health..."
    if [ -f "check_bot_status.py" ]; then
        python3 check_bot_status.py
    else
        echo "❌ check_bot_status.py not found"
    fi

    echo ""
    echo "📁 Checking project files..."
    required_files=("render.yaml" "requirements.txt" "rudeai_bot/webhook_server.py")

    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            echo "   ✅ $file"
        else
            echo "   ❌ $file (missing)"
        fi
    done

    echo ""
    echo "🐍 Python requirements:"
    if [ -f "requirements.txt" ]; then
        echo "   ✅ requirements.txt found"
        echo "   📋 Key dependencies:"
        grep -E "(fastapi|uvicorn|python-telegram-bot|openai|sqlalchemy)" requirements.txt || echo "   ⚠️  Check requirements.txt for missing dependencies"
    else
        echo "   ❌ requirements.txt not found!"
    fi
}

# Main script logic
case "${1:-help}" in
    "setup")
        show_setup
        ;;
    "env")
        show_env
        ;;
    "check")
        run_diagnostics
        ;;
    "webhook")
        generate_webhook
        ;;
    "help")
        show_help
        ;;
    *)
        show_help
        echo ""
        echo "❌ Unknown command: $1"
        exit 1
        ;;
esac