#!/bin/bash

# RUDE.AI Railway Deployment Script
# This script helps you deploy to Railway quickly

echo "🚀 RUDE.AI Railway Deployment Helper"
echo "===================================="

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📝 Initializing git repository..."
    git init
    git add .
    git commit -m "🚀 Initial RUDE.AI bot deployment

✨ Features:
- Enhanced 10-level rudeness personality system
- Context awareness and excuse detection
- Production-ready infrastructure
- Railway deployment configuration

🔧 Infrastructure:
- FastAPI webhook server
- PostgreSQL database support
- Comprehensive monitoring
- Rate limiting and security"
else
    echo "✅ Git repository already initialized"
fi

echo ""
echo "📋 Next Steps:"
echo "1. Create a GitHub repository at: https://github.com/new"
echo "2. Add your GitHub remote:"
echo "   git remote add origin https://github.com/YOUR_USERNAME/rudeai-bot.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "3. Deploy to Railway:"
echo "   - Go to https://railway.app"
echo "   - Sign in with GitHub"
echo "   - Click 'New Project' → 'Deploy from GitHub repo'"
echo "   - Select your rudeai-bot repository"
echo ""
echo "4. Add PostgreSQL database:"
echo "   - In Railway project, click '+ New' → 'Database' → 'PostgreSQL'"
echo ""
echo "5. Set environment variables in Railway dashboard:"
echo "   OPENAI_API_KEY=your_openai_api_key_here"
echo "   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here"
echo "   WEBHOOK_SECRET=12b3114962ebffc8a8ac1a5868a5b9c1077cead95588ee7497bdcccdd73ed6b7"
echo "   ENVIRONMENT=production"
echo ""
echo "📖 For detailed instructions, see: RAILWAY_DEPLOYMENT.md"
echo "✅ Your bot will be live in 2-3 minutes after deployment!"