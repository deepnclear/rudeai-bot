#!/bin/bash

# Railway deployment script for RUDE.AI bot
# This script helps with Railway deployment and troubleshooting

set -e

echo "🚂 RAILWAY DEPLOYMENT HELPER"
echo "=============================="

# Check if we're in the right directory
if [ ! -f "railway.toml" ]; then
    echo "❌ Error: railway.toml not found. Run this script from the project root."
    exit 1
fi

# Function to check if Railway CLI is installed
check_railway_cli() {
    if ! command -v railway &> /dev/null; then
        echo "⚠️  Railway CLI not found. Installing..."
        echo "📥 Visit: https://docs.railway.app/develop/cli#installation"
        echo ""
        echo "Quick install options:"
        echo "  macOS: brew install railway/tap/cli"
        echo "  Linux/WSL: curl -fsSL https://railway.app/install.sh | sh"
        echo ""
        read -p "Press Enter after installing Railway CLI..."

        if ! command -v railway &> /dev/null; then
            echo "❌ Railway CLI still not found. Please install it first."
            exit 1
        fi
    fi
    echo "✅ Railway CLI found"
}

# Function to deploy to Railway
deploy() {
    echo ""
    echo "🚀 DEPLOYING TO RAILWAY"
    echo "======================"

    # Login check
    if ! railway whoami &> /dev/null; then
        echo "🔐 Logging into Railway..."
        railway login
    else
        echo "✅ Already logged into Railway"
    fi

    # Deploy
    echo "📦 Deploying application..."
    railway up --detach

    echo ""
    echo "✅ Deployment initiated!"
    echo ""
    echo "📊 Monitor deployment:"
    echo "  railway logs"
    echo "  railway status"
    echo ""
    echo "🌐 Get domain:"
    echo "  railway domain"
    echo ""
}

# Function to setup environment variables
setup_env() {
    echo ""
    echo "🔧 ENVIRONMENT SETUP"
    echo "===================="

    echo "Setting up Railway environment variables..."

    # Check if .env.railway exists
    if [ ! -f ".env.railway" ]; then
        echo "❌ .env.railway file not found!"
        exit 1
    fi

    echo "📋 Required environment variables:"
    echo "  - OPENAI_API_KEY"
    echo "  - TELEGRAM_BOT_TOKEN"
    echo "  - WEBHOOK_SECRET"
    echo ""
    echo "💡 Set these in Railway dashboard → Variables"
    echo "   Or use: railway variables set KEY=value"
    echo ""

    # Show webhook secret
    webhook_secret=$(grep "WEBHOOK_SECRET=" .env.railway | cut -d'=' -f2)
    echo "🔐 Your webhook secret: $webhook_secret"
    echo ""
}

# Function to run diagnostics
diagnostics() {
    echo ""
    echo "🔍 RUNNING DIAGNOSTICS"
    echo "====================="

    echo "📊 Checking application health..."
    python3 check_bot_status.py

    echo ""
    echo "🔧 Railway project info:"
    if command -v railway &> /dev/null; then
        railway status 2>/dev/null || echo "❌ Not connected to Railway project"
        railway domain 2>/dev/null || echo "❌ No domain assigned"
    else
        echo "❌ Railway CLI not installed"
    fi
}

# Function to show logs
logs() {
    echo ""
    echo "📜 RAILWAY LOGS"
    echo "==============="

    if command -v railway &> /dev/null; then
        echo "Fetching latest logs..."
        railway logs --tail 50
    else
        echo "❌ Railway CLI not installed"
    fi
}

# Function to show help
show_help() {
    echo ""
    echo "🤖 RUDE.AI RAILWAY DEPLOYMENT"
    echo "=============================="
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  deploy      Deploy to Railway"
    echo "  env         Setup environment variables"
    echo "  check       Run diagnostics"
    echo "  logs        Show Railway logs"
    echo "  help        Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 deploy        # Deploy the bot"
    echo "  $0 check         # Check bot status"
    echo "  $0 logs          # View logs"
    echo ""
}

# Main script logic
case "${1:-help}" in
    "deploy")
        check_railway_cli
        deploy
        ;;
    "env")
        setup_env
        ;;
    "check")
        diagnostics
        ;;
    "logs")
        logs
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