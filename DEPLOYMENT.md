# RUDE.AI Bot - Production Deployment Guide

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- SSL certificate for your domain
- Telegram Bot Token (from @BotFather)
- OpenAI API Key

### 1. Clone and Setup
```bash
git clone <your-repo>
cd rudeai-bot

# Copy environment file
cp .env.example .env
```

### 2. Configure Environment Variables
Edit `.env` with your production values:

```bash
# Required
OPENAI_API_KEY=your_openai_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
WEBHOOK_URL=https://your-domain.com
WEBHOOK_SECRET=generate_random_32_char_string
POSTGRES_PASSWORD=secure_database_password

# Optional (has defaults)
ENVIRONMENT=production
LOG_LEVEL=INFO
RATE_LIMIT_PER_MINUTE=10
```

### 3. SSL Certificate Setup
```bash
# Create SSL directory
mkdir -p nginx/ssl

# Copy your SSL certificates
cp /path/to/fullchain.pem nginx/ssl/
cp /path/to/privkey.pem nginx/ssl/

# Update domain in nginx.conf
sed -i 's/your-domain.com/actual-domain.com/g' nginx/nginx.conf
```

### 4. Deploy
```bash
# Production deployment
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs rudeai-bot
```

### 5. Set Telegram Webhook
The webhook will be automatically set when the service starts, but you can verify:
```bash
curl -X GET "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo"
```

## 🔧 Development Setup

```bash
# Development environment
cp .env.dev .env.local
# Edit .env.local with your API keys

# Run development server
docker-compose -f docker-compose.dev.yml up

# Or run locally
pip install -r requirements.txt
uvicorn rudeai_bot.webhook_server:app --reload
```

## 📊 Monitoring

### Health Checks
- Health endpoint: `https://your-domain.com/health`
- Metrics endpoint: `https://your-domain.com/metrics` (restricted)

### Logs
```bash
# View logs
docker-compose logs -f rudeai-bot

# Log files (inside container)
/app/logs/rudeai.log      # Main application logs
/app/logs/errors.log      # Error logs only
/app/logs/access.log      # Webhook access logs
```

### Log Analysis
Production logs are in JSON format for easy parsing:
```bash
# Find rate limiting events
docker-compose exec rudeai-bot grep "rate_limit" logs/rudeai.log

# Monitor AI service performance
docker-compose exec rudeai-bot grep "ai_service_call" logs/rudeai.log | jq '.response_time_ms'

# Track user interactions
docker-compose exec rudeai-bot grep "user_interaction" logs/rudeai.log | jq '.rudeness_level'
```

## 🛡️ Security Features

### Rate Limiting
- **Webhook**: 5 requests/second per IP
- **General API**: 10 requests/second per IP
- **User-specific**: 10 messages/minute per user

### Network Security
- HTTPS only (HTTP redirects to HTTPS)
- Restricted metrics endpoint (internal networks only)
- Security headers (HSTS, XSS protection, etc.)

### Application Security
- Non-root container user
- Input validation on all endpoints
- SQL injection protection via SQLAlchemy
- Environment-based configuration

## 🔄 Database Management

### Backup PostgreSQL
```bash
# Create backup
docker-compose exec postgres pg_dump -U rudeai rudeai_db > backup.sql

# Restore backup
docker-compose exec -T postgres psql -U rudeai rudeai_db < backup.sql
```

### Migrations
```bash
# Run migrations (if needed)
docker-compose exec rudeai-bot alembic upgrade head
```

## 📈 Scaling

### Horizontal Scaling
```bash
# Scale to multiple instances
docker-compose up -d --scale rudeai-bot=3

# Update nginx upstream in nginx.conf:
upstream rudeai_backend {
    server rudeai-bot_rudeai-bot_1:8000;
    server rudeai-bot_rudeai-bot_2:8000;
    server rudeai-bot_rudeai-bot_3:8000;
}
```

### Database Scaling
- Use PostgreSQL read replicas for analytics
- Consider connection pooling (pgbouncer)
- Monitor database performance

## 🚨 Troubleshooting

### Common Issues

**Webhook not working:**
```bash
# Check webhook status
curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo"

# Reset webhook
curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook?url=https://your-domain.com/webhook/YOUR_SECRET"
```

**High memory usage:**
```bash
# Check container resources
docker stats

# Increase memory limits in docker-compose.yml
services:
  rudeai-bot:
    deploy:
      resources:
        limits:
          memory: 512M
```

**Rate limiting issues:**
```bash
# Check rate limit logs
docker-compose logs rudeai-bot | grep "rate_limit"

# Adjust rate limits in .env
RATE_LIMIT_PER_MINUTE=20
```

### Performance Monitoring
```bash
# Monitor response times
docker-compose logs rudeai-bot | grep "processing_time_ms" | tail -100

# Check error rates
docker-compose logs rudeai-bot | grep "ERROR" | wc -l

# Monitor user activity
docker-compose logs rudeai-bot | grep "user_interaction" | tail -50
```

## 🔧 Maintenance

### Regular Tasks
1. **Monitor logs** for errors and performance issues
2. **Update dependencies** regularly for security
3. **Backup database** daily
4. **Monitor disk space** (logs can grow large)
5. **Review rate limiting** based on usage patterns

### Updates
```bash
# Update application
git pull
docker-compose build rudeai-bot
docker-compose up -d rudeai-bot

# Update dependencies
docker-compose build --no-cache rudeai-bot
```

## 📞 Support

For issues:
1. Check logs: `docker-compose logs rudeai-bot`
2. Verify configuration: `.env` file settings
3. Test webhook: Use health endpoint
4. Monitor resources: `docker stats`

## 🔒 Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ENVIRONMENT` | No | development | Environment (development/staging/production) |
| `OPENAI_API_KEY` | Yes | - | OpenAI API key |
| `TELEGRAM_BOT_TOKEN` | Yes | - | Telegram bot token |
| `WEBHOOK_URL` | Yes* | - | Public webhook URL (*required for production) |
| `WEBHOOK_SECRET` | Yes* | - | Webhook security token (*required for production) |
| `DATABASE_URL` | No | SQLite | Database connection URL |
| `LOG_LEVEL` | No | INFO | Logging level (DEBUG/INFO/WARNING/ERROR) |
| `RATE_LIMIT_PER_MINUTE` | No | 10 | User message rate limit |
| `MAX_MESSAGE_LENGTH` | No | 1000 | Maximum message length |