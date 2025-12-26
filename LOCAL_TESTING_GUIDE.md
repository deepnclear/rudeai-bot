# 🏠 Local Testing Guide for RUDE.AI Bot

Test your RUDE.AI Telegram bot locally using ngrok for webhooks before deploying to any cloud platform.

## ✅ Why Test Locally?

- **No deployment needed** - Test everything on your Mac first
- **Instant feedback** - See logs and debug in real-time
- **Free testing** - No cloud costs during development
- **Perfect debugging** - Full control over the environment
- **Validate before deploy** - Ensure everything works before going live

## 🚀 Quick Start

### Step 1: Install ngrok

**Option 1 - Direct Download (Recommended):**
1. Go to [ngrok.com/download](https://ngrok.com/download)
2. Download ngrok for macOS
3. Unzip and install:
   ```bash
   unzip ~/Downloads/ngrok-*.zip
   sudo mv ngrok /usr/local/bin/
   ```

**Option 2 - Homebrew (if you have it):**
```bash
brew install ngrok/ngrok/ngrok
```

### Step 2: Authenticate ngrok
1. Sign up at [ngrok.com](https://dashboard.ngrok.com/signup) (free)
2. Get your auth token from [dashboard](https://dashboard.ngrok.com/get-started/your-authtoken)
3. Configure ngrok:
   ```bash
   ngrok config add-authtoken YOUR_AUTH_TOKEN
   ```

### Step 3: Set Up Environment
1. **Copy environment template:**
   ```bash
   cp .env.local .env
   ```

2. **Edit `.env` with your API keys:**
   ```bash
   nano .env  # or use any text editor
   ```

   **Required changes:**
   ```bash
   OPENAI_API_KEY=sk-your-actual-openai-key-here
   TELEGRAM_BOT_TOKEN=123456789:your-actual-bot-token-here
   ```

   **Get your keys:**
   - OpenAI API Key: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
   - Telegram Bot Token: Message [@BotFather](https://t.me/BotFather) on Telegram

### Step 4: Install Python Dependencies
```bash
# Create virtual environment (if you don't have one)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 5: Start Testing

**Terminal 1 - Start ngrok tunnel:**
```bash
./start_ngrok.sh
```

**Terminal 2 - Start bot server:**
```bash
./start_bot.sh
```

**Terminal 3 - Test endpoints:**
```bash
./test_bot.sh
```

## 📱 Testing Your Bot

### 1. Verify Local Setup
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test webhook endpoint structure
curl http://localhost:8000/status
```

### 2. Get Your Public URL
When you run `./start_ngrok.sh`, you'll see:
```
✅ ngrok tunnel is active!
   Local URL:  http://localhost:8000
   Public URL: https://abc123.ngrok-free.app

🔗 Webhook URL for Telegram:
   https://abc123.ngrok-free.app/webhook/local-development-secret-12345
```

### 3. Test with Telegram
1. **Send a message to your bot** on Telegram
2. **Check Terminal 2** for webhook logs:
   ```
   🔍 HEALTH CHECK REQUEST:
      From: 1.2.3.4
      Host: abc123.ngrok-free.app
   ✅ Health check response: {...}
   ```

3. **Monitor ngrok dashboard** at [localhost:4040](http://localhost:4040)

## 🔧 Helpful Commands

### Start Everything
```bash
# All-in-one testing
./start_ngrok.sh &     # Start tunnel in background
sleep 5                # Wait for ngrok
./start_bot.sh &       # Start bot in background
sleep 3                # Wait for bot
./test_bot.sh          # Run tests
```

### Stop Everything
```bash
# Kill all processes
pkill -f ngrok
pkill -f uvicorn
```

### Check Status
```bash
# Test all endpoints
./test_bot.sh

# Check ngrok status
curl localhost:4040/api/tunnels | python3 -m json.tool

# Check bot health
curl localhost:8000/health | python3 -m json.tool
```

### View Logs
```bash
# Real-time bot logs (Terminal 2)
# ngrok request logs at: http://localhost:4040

# Check database
ls -la rudeai_bot_local.db*
```

## 🐛 Troubleshooting

### Common Issues

**Bot doesn't respond to messages:**
- ✅ Check ngrok is running: `curl localhost:4040/api/tunnels`
- ✅ Verify webhook URL in .env matches ngrok URL
- ✅ Check bot logs in Terminal 2 for incoming requests
- ✅ Ensure API keys are correctly set in .env

**"ngrok not found":**
- Install ngrok following Step 1 above
- Check installation: `which ngrok`

**"Authentication failed":**
- Sign up at ngrok.com and get auth token
- Run: `ngrok config add-authtoken YOUR_TOKEN`

**"Service unavailable":**
- Check API keys are valid (not placeholder values)
- Check OpenAI API key starts with `sk-`
- Check Telegram token contains `:`

**Bot server won't start:**
- Check Python dependencies: `pip install -r requirements.txt`
- Check .env file exists and has real API keys
- Check port 8000 isn't already in use: `lsof -i :8000`

### Debug Commands

```bash
# Test API keys work
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('OpenAI key:', os.getenv('OPENAI_API_KEY', 'NOT SET')[:10] + '...')
print('Telegram token:', os.getenv('TELEGRAM_BOT_TOKEN', 'NOT SET')[:10] + '...')
"

# Test database connection
python3 -c "
from rudeai_bot.database.base import engine
print('Database:', engine.url)
"

# Check webhook URL
grep WEBHOOK_URL .env
```

## 📊 Monitoring

### ngrok Dashboard
- URL: [localhost:4040](http://localhost:4040)
- Shows all HTTP requests to your tunnel
- Great for debugging webhook calls

### Bot Endpoints
- Health: [localhost:8000/health](http://localhost:8000/health)
- Status: [localhost:8000/status](http://localhost:8000/status)
- Root: [localhost:8000/](http://localhost:8000/)
- Ping: [localhost:8000/ping](http://localhost:8000/ping)

### Logs to Watch
1. **Terminal 2** - Bot server logs (webhook requests, AI responses)
2. **ngrok dashboard** - HTTP traffic to your tunnel
3. **Terminal 3** - Test results and endpoint responses

## 🔄 Development Workflow

### Making Changes
1. **Edit code** in your IDE
2. **Save files** - uvicorn auto-reloads
3. **Test immediately** - no restart needed
4. **Check logs** for any errors

### Testing New Features
1. **Add new endpoint** to webhook_server.py
2. **Test locally**: `curl localhost:8000/your-endpoint`
3. **Test via ngrok**: Check ngrok dashboard
4. **Test with Telegram** if webhook-related

### Database Changes
```bash
# Reset local database
rm rudeai_bot_local.db*

# Restart bot to recreate tables
# (Ctrl+C in Terminal 2, then ./start_bot.sh)
```

## 📁 File Overview

```
rudeai-bot/
├── .env                    # Your API keys (edit this!)
├── .env.local             # Template (don't edit)
├── start_ngrok.sh         # Start ngrok tunnel
├── start_bot.sh           # Start bot server
├── test_bot.sh            # Test all endpoints
├── quick_local_setup.sh   # One-time setup
└── rudeai_bot_local.db    # Local SQLite database
```

## 🎯 Success Checklist

Before deploying to cloud:

- [ ] ✅ ngrok tunnel shows HTTPS URL
- [ ] ✅ Bot server starts without errors
- [ ] ✅ All test endpoints return 200 OK
- [ ] ✅ Bot responds to Telegram messages
- [ ] ✅ Webhook requests visible in ngrok dashboard
- [ ] ✅ AI responses working (check OpenAI key)
- [ ] ✅ Database storing conversations
- [ ] ✅ No error messages in bot logs

## 🚀 Next Steps

Once everything works locally:
1. **Deploy to Render** using `RENDER_DEPLOYMENT.md`
2. **Or deploy to Railway** using `RAILWAY_DEPLOYMENT.md`
3. **Set production environment variables**
4. **Update webhook URL** to production domain

---

**🎉 Happy Local Testing!** Your bot is now running locally with full webhook support and real-time debugging capabilities.