import asyncio
import json
import os
from typing import Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from telegram import Update
from telegram.ext import Application
from loguru import logger
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from rudeai_bot.config.settings import settings
from rudeai_bot.services.ai_service import AIService
from rudeai_bot.handlers.bot_handlers import BotHandlers
from rudeai_bot.database.base import engine, Base
from rudeai_bot.utils.logger import setup_logging


class WebhookServer:
    def __init__(self):
        self.app = FastAPI(
            title="RUDE.AI Bot",
            description="Telegram Bot with Webhook Support",
            version="1.0.0"
        )
        self.ai_service = AIService()
        self.handlers = BotHandlers(self.ai_service)
        self.telegram_app = None

        # Rate limiting
        self.limiter = Limiter(key_func=get_remote_address)
        self.app.state.limiter = self.limiter
        self.app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

        # User-specific rate limiting
        self.user_requests = defaultdict(list)
        self.setup_routes()
        self.setup_database()

    def setup_database(self):
        """Initialize database tables"""
        try:
            logger.info(f"Connecting to database: {settings.database_url[:50]}...")
            Base.metadata.create_all(bind=engine)
            logger.info("✅ Database tables created successfully")
        except Exception as e:
            logger.error(f"❌ Database setup failed: {e}")
            raise

    def setup_telegram_app(self) -> Application:
        """Setup Telegram application with handlers"""
        application = Application.builder().token(settings.telegram_bot_token).build()

        # Don't add handlers here - webhook will handle updates directly
        application.add_error_handler(self.handlers.error_handler)

        logger.info("Telegram application configured for webhook mode")
        return application

    def check_user_rate_limit(self, user_id: int) -> bool:
        """Check if user is within rate limits"""
        now = datetime.now()
        cutoff = now - timedelta(minutes=1)

        # Clean old requests
        self.user_requests[user_id] = [
            req_time for req_time in self.user_requests[user_id]
            if req_time > cutoff
        ]

        # Check if user has exceeded limit (10 requests per minute)
        if len(self.user_requests[user_id]) >= 10:
            return False

        self.user_requests[user_id].append(now)
        return True

    def setup_routes(self):
        """Setup FastAPI routes"""

        @self.app.get("/health")
        @self.limiter.limit("30/minute")
        async def health_check(request: Request):
            """Health check endpoint for monitoring"""
            try:
                # Test database connection
                from rudeai_bot.database.base import get_db
                with next(get_db()) as db:
                    db.execute("SELECT 1")

                # Test AI service
                ai_status = "healthy" if self.ai_service.client else "unhealthy"

                return JSONResponse({
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "database": "connected",
                    "ai_service": ai_status,
                    "environment": settings.environment
                })
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                raise HTTPException(status_code=503, detail="Service unhealthy")

        @self.app.get("/metrics")
        @self.limiter.limit("10/minute")
        async def metrics(request: Request):
            """Basic metrics endpoint"""
            try:
                from rudeai_bot.database.base import get_db
                from rudeai_bot.database.operations import DatabaseOperations

                with next(get_db()) as db:
                    db_ops = DatabaseOperations(db)
                    # Get basic stats
                    total_users = db.execute("SELECT COUNT(*) FROM users").scalar()
                    total_conversations = db.execute("SELECT COUNT(*) FROM conversations").scalar()

                return JSONResponse({
                    "total_users": total_users,
                    "total_conversations": total_conversations,
                    "active_requests": len(self.user_requests),
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Metrics endpoint failed: {e}")
                raise HTTPException(status_code=500, detail="Metrics unavailable")

        @self.app.post(f"/webhook/{settings.webhook_secret}")
        @self.limiter.limit("100/minute")
        async def webhook(request: Request):
            """Webhook endpoint for Telegram updates"""
            try:
                # Parse the update
                body = await request.body()
                data = json.loads(body.decode())
                update = Update.de_json(data, self.telegram_app.bot)

                if not update or not update.effective_user:
                    return JSONResponse({"status": "ignored"})

                # Check user rate limits
                user_id = update.effective_user.id
                if not self.check_user_rate_limit(user_id):
                    logger.warning(f"Rate limit exceeded for user {user_id}")
                    if update.message:
                        await update.message.reply_text(
                            "Slow down! You're sending too many messages. Wait a minute."
                        )
                    return JSONResponse({"status": "rate_limited"})

                # Log the update
                logger.info(f"Received update from user {user_id}: {update.update_id}")

                # Process the update
                await self.process_update(update)

                return JSONResponse({"status": "ok"})

            except json.JSONDecodeError:
                logger.error("Invalid JSON in webhook request")
                raise HTTPException(status_code=400, detail="Invalid JSON")
            except Exception as e:
                logger.error(f"Error processing webhook: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @self.app.get("/")
        async def root():
            """Root endpoint"""
            return JSONResponse({
                "service": "RUDE.AI Bot",
                "status": "running",
                "version": "1.0.0"
            })

    async def process_update(self, update: Update):
        """Process a Telegram update"""
        try:
            if update.message and update.message.text:
                text = update.message.text

                # Handle commands
                if text.startswith('/start'):
                    await self.handlers.start_command(update, None)
                elif text.startswith('/help'):
                    await self.handlers.help_command(update, None)
                elif text.startswith('/stats'):
                    await self.handlers.stats_command(update, None)
                elif text.startswith('/rudeness'):
                    # Parse rudeness level from command
                    parts = text.split()
                    if len(parts) > 1:
                        # Create a mock context with args
                        class MockContext:
                            def __init__(self, args):
                                self.args = args
                        context = MockContext([parts[1]])
                        await self.handlers.rudeness_command(update, context)
                    else:
                        await self.handlers.rudeness_command(update, MockContext([]))
                else:
                    # Handle regular message
                    await self.handlers.handle_message(update, None)

        except Exception as e:
            logger.error(f"Error processing update {update.update_id}: {e}")
            if update.message:
                await update.message.reply_text(
                    "Something went wrong. Even I have limits, apparently."
                )

    async def setup_webhook(self):
        """Set up the webhook with Telegram"""
        try:
            # Auto-detect Railway environment
            railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN')
            if railway_domain:
                webhook_url = f"https://{railway_domain}/webhook/{settings.webhook_secret}"
                logger.info(f"Railway environment detected: {railway_domain}")
            else:
                webhook_url = f"{settings.webhook_url}/webhook/{settings.webhook_secret}"

            await self.telegram_app.bot.set_webhook(
                url=webhook_url,
                drop_pending_updates=True,
                allowed_updates=["message", "callback_query"]
            )
            logger.info(f"Webhook set up successfully: {webhook_url}")

            # Log webhook info for debugging
            webhook_info = await self.telegram_app.bot.get_webhook_info()
            logger.info(f"Webhook status: URL={webhook_info.url}, Pending={webhook_info.pending_update_count}")

        except Exception as e:
            logger.error(f"Failed to set up webhook: {e}")
            raise

    async def startup(self):
        """Initialize the webhook server"""
        setup_logging()
        logger.info("🚀 Starting RUDE.AI Webhook Server...")

        # Log environment info
        logger.info(f"🌍 Environment: {settings.environment}")
        logger.info(f"🌐 Railway Domain: {os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'Not detected')}")
        logger.info(f"🔧 Port: {os.environ.get('PORT', 'Not set')}")
        logger.info(f"🔑 OpenAI Model: {settings.openai_model}")

        try:
            self.telegram_app = self.setup_telegram_app()
            logger.info("✅ Telegram app configured")

            await self.telegram_app.initialize()
            logger.info("✅ Telegram app initialized")

            await self.telegram_app.start()
            logger.info("✅ Telegram app started")

            # Set up webhook
            await self.setup_webhook()
            logger.info("✅ Webhook configured")

            logger.info("🎉 Webhook server is ready!")
        except Exception as e:
            logger.error(f"❌ Startup failed: {e}")
            raise

    async def shutdown(self):
        """Cleanup on shutdown"""
        try:
            if self.telegram_app:
                await self.telegram_app.bot.delete_webhook()
                await self.telegram_app.stop()
                await self.telegram_app.shutdown()

            await self.ai_service.close()
            logger.info("Webhook server stopped successfully")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

    def get_app(self) -> FastAPI:
        """Get the FastAPI application"""
        return self.app


# Global server instance
webhook_server = WebhookServer()
app = webhook_server.get_app()


# Lifespan events
@app.on_event("startup")
async def startup_event():
    await webhook_server.startup()


@app.on_event("shutdown")
async def shutdown_event():
    await webhook_server.shutdown()