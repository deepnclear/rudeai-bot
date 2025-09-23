# 🚀 Railway Deployment Guide - RUDE.AI Bot

## Quick Deploy to Railway (Free Tier)

### Prerequisites
- GitHub account
- Railway account (sign up at [railway.app](https://railway.app))
- Your API keys (already configured in this project)

---

## 🎯 **Step 1: Prepare GitHub Repository**

### 1.1 Create GitHub Repository
```bash
# Initialize git (if not already done)
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

# Create repository on GitHub and push
git remote add origin https://github.com/YOUR_USERNAME/rudeai-bot.git
git branch -M main
git push -u origin main
```

---

## 🛤️ **Step 2: Deploy to Railway**

### 2.1 Connect to Railway
1. Go to [railway.app](https://railway.app)
2. Sign in with GitHub
3. Click **"New Project"**
4. Select **"Deploy from GitHub repo"**
5. Choose your `rudeai-bot` repository

### 2.2 Configure Services

Railway will automatically detect your project. You'll need to set up:

1. **Web Service** (your bot)
2. **PostgreSQL Database** (free tier)

---

## ⚙️ **Step 3: Environment Variables**

### 3.1 Add Environment Variables in Railway Dashboard

Navigate to your project → **Variables** and add:

```bash
# Required API Keys
OPENAI_API_KEY=your_openai_api_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Webhook Configuration (Railway auto-assigns domain)
WEBHOOK_SECRET=12b3114962ebffc8a8ac1a5868a5b9c1077cead95588ee7497bdcccdd73ed6b7

# Application Settings
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Security
RATE_LIMIT_PER_MINUTE=20
MAX_MESSAGE_LENGTH=1000

# Monitoring
ENABLE_METRICS=true
METRICS_RETENTION_DAYS=7
```

### 3.2 Database Configuration (Automatic)

Railway will automatically provide:
- `DATABASE_URL` - PostgreSQL connection string
- `PORT` - Dynamic port assignment

---

## 🗄️ **Step 4: PostgreSQL Database Setup**

### 4.1 Add PostgreSQL Service
1. In your Railway project, click **"+ New"**
2. Select **"Database"** → **"PostgreSQL"**
3. Railway will automatically create and link the database

### 4.2 Database will provide:
- **DATABASE_URL**: Automatic connection string
- **Free Tier**: 100 hours/month (sufficient for most bots)

---

## 🌐 **Step 5: Webhook Configuration**

### 5.1 Get Your Railway Domain
After deployment, Railway provides a URL like:
```
https://your-app-name-production-abc123.up.railway.app
```

### 5.2 Update Webhook URL
Add this to your Railway environment variables:
```bash
WEBHOOK_URL=https://your-app-name-production-abc123.up.railway.app
```

### 5.3 Automatic Webhook Setup
Your bot includes automatic webhook configuration! It will:
1. Detect the Railway domain
2. Set up the Telegram webhook automatically
3. Verify the connection

---

## 🚀 **Step 6: Deploy & Test**

### 6.1 Deploy
1. Railway will automatically deploy when you push to GitHub
2. Monitor the build logs in Railway dashboard
3. Wait for deployment to complete (usually 2-3 minutes)

### 6.2 Test Your Bot
1. Find your bot on Telegram (search for the name you gave @BotFather)
2. Send `/start` command
3. Test the enhanced features:
   ```
   /help - See all commands
   /stats - View your stats
   /rudeness 7 - Set rudeness to level 7
   Send any message to test the AI
   ```

---

## 📊 **Step 7: Monitoring & Management**

### 7.1 Railway Dashboard
Monitor your deployment:
- **Deployments**: View build/deploy status
- **Metrics**: CPU, memory, network usage
- **Logs**: Real-time application logs

### 7.2 Health Checks
Your bot includes built-in health monitoring:
```bash
# Health endpoint
https://your-domain.up.railway.app/health

# Metrics endpoint (restricted)
https://your-domain.up.railway.app/metrics
```

---

## 🎛️ **Step 8: Advanced Configuration**

### 8.1 Custom Domain (Optional)
1. Purchase a domain
2. In Railway dashboard: **Settings** → **Domains**
3. Add your custom domain
4. Update `WEBHOOK_URL` environment variable

### 8.2 Scaling (If Needed)
Railway free tier includes:
- **500 hours/month** execution time
- **1GB RAM**
- **1 vCPU**
- **100GB bandwidth**

Upgrade to **Pro** if you need more resources.

---

## 🔧 **Troubleshooting**

### Common Issues

**1. Webhook not working:**
```bash
# Check webhook status in logs
# Railway dashboard → Logs → Search for "webhook"

# Manually set webhook
curl -X POST "https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://your-domain.up.railway.app/webhook/YOUR_SECRET"}'
```

**2. Database connection errors:**
- Verify `DATABASE_URL` is set in Railway variables
- Check PostgreSQL service is running

**3. Environment variables not loading:**
- Verify all variables are set in Railway dashboard
- Redeploy after adding new variables

**4. Build failures:**
- Check Railway build logs
- Verify `requirements.txt` is up to date
- Ensure Python version compatibility

---

## 🎉 **Success! Your Bot is Live**

### What You've Accomplished:
✅ **Production-ready bot** deployed to Railway
✅ **Free PostgreSQL database** configured
✅ **Auto-deployment** from GitHub
✅ **Enhanced RUDE.AI features** active
✅ **Monitoring and health checks** operational
✅ **Secure webhook** configured

### Your Bot Features:
🤖 **10-level rudeness control** (1=mild, 10=savage)
🧠 **Context awareness** with conversation memory
🎯 **Excuse detection** with automatic escalation
📊 **User analytics** and interaction tracking
⚡ **High-performance** webhook infrastructure

---

## 💡 **Pro Tips**

1. **Monitor usage** in Railway dashboard to stay within free tier
2. **Use `/stats`** command to track user engagement
3. **Check health endpoint** regularly for system status
4. **Review logs** for any errors or issues
5. **Update rudeness levels** based on user feedback

Your RUDE.AI bot is now live and ready to brutally motivate users! 🚀⚡