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
        self.setup_events()

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
        from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters

        application = Application.builder().token(settings.telegram_bot_token).build()

        # Task creation conversation handler
        task_conversation = ConversationHandler(
            entry_points=[CommandHandler("new", self.handlers.new_task_command)],
            states={
                self.handlers.TASK_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.task_name_received)
                ],
                self.handlers.TASK_HATE_LEVEL: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.task_hate_level_received)
                ],
                self.handlers.TASK_PRIORITY: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.task_priority_received)
                ],
            },
            fallbacks=[CommandHandler("cancel", self.handlers.cancel_task_creation)],
            name="task_creation",
            persistent=False,
        )

        application.add_handler(task_conversation)

        # Task completion conversation handler
        done_conversation = ConversationHandler(
            entry_points=[CommandHandler("done", self.handlers.done_command)],
            states={
                self.handlers.TASK_SELECTION: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.task_selection_received)
                ],
            },
            fallbacks=[CommandHandler("cancel", self.handlers.cancel_task_completion)],
            name="task_completion",
            persistent=False,
        )

        application.add_handler(done_conversation)

        # Regular command handlers
        application.add_handler(CommandHandler("start", self.handlers.start_command))
        application.add_handler(CommandHandler("help", self.handlers.help_command))
        application.add_handler(CommandHandler("list", self.handlers.list_tasks_command))
        application.add_handler(CommandHandler("stats", self.handlers.stats_command))
        application.add_handler(CommandHandler("rudeness", self.handlers.rudeness_command))

        # Message handler (must be last)
        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.handle_message)
        )

        application.add_error_handler(self.handlers.error_handler)

        logger.info("Telegram application configured for webhook mode with all handlers")
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
        async def health_check(request: Request):
            """Railway health check endpoint with detailed logging"""
            try:
                # Log every health check request for debugging
                client_ip = request.client.host if request.client else "unknown"
                user_agent = request.headers.get("user-agent", "unknown")
                host_header = request.headers.get("host", "unknown")

                logger.info(f"🔍 HEALTH CHECK REQUEST:")
                logger.info(f"   From: {client_ip}")
                logger.info(f"   Host: {host_header}")
                logger.info(f"   User-Agent: {user_agent}")
                logger.info(f"   Headers: {dict(request.headers)}")

                # Check if this is Railway's health checker
                is_railway_healthcheck = (
                    "healthcheck.railway.app" in host_header or
                    "railway" in user_agent.lower()
                )

                if is_railway_healthcheck:
                    logger.info("🚂 Railway health check detected!")

                response_data = {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "port": os.environ.get('PORT', '8000'),
                    "host": os.environ.get('HOST', '0.0.0.0'),
                    "railway_domain": os.environ.get('RAILWAY_PUBLIC_DOMAIN'),
                    "environment": settings.environment
                }

                logger.info(f"✅ Health check response: {response_data}")

                return JSONResponse(
                    status_code=200,
                    content=response_data
                )

            except Exception as e:
                logger.error(f"❌ Health check error: {e}")
                # Still return 200 for Railway compatibility
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "degraded",
                        "timestamp": datetime.now().isoformat(),
                        "error": str(e)
                    }
                )

        @self.app.get("/")
        async def root(request: Request):
            """Root endpoint for basic connectivity check with logging"""
            client_ip = request.client.host if request.client else "unknown"
            logger.info(f"📍 Root endpoint accessed from: {client_ip}")

            return JSONResponse(
                status_code=200,
                content={
                    "service": "RUDE.AI Bot",
                    "status": "running",
                    "timestamp": datetime.now().isoformat(),
                    "port": os.environ.get('PORT', '8000'),
                    "host": os.environ.get('HOST', '0.0.0.0'),
                    "railway_domain": os.environ.get('RAILWAY_PUBLIC_DOMAIN')
                }
            )

        @self.app.get("/ping")
        async def ping():
            """Simple ping endpoint for testing"""
            logger.info("🏓 Ping endpoint accessed")
            return JSONResponse(status_code=200, content={"ping": "pong"})

        @self.app.get("/status")
        async def status():
            """Detailed status endpoint for debugging"""
            logger.info("📊 Status endpoint accessed")
            return JSONResponse(
                status_code=200,
                content={
                    "service": "RUDE.AI Bot",
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "environment": settings.environment,
                    "port": os.environ.get('PORT', '8000'),
                    "host": os.environ.get('HOST', '0.0.0.0'),
                    "railway": {
                        "domain": os.environ.get('RAILWAY_PUBLIC_DOMAIN'),
                        "project_id": os.environ.get('RAILWAY_PROJECT_ID'),
                        "deployment_id": os.environ.get('RAILWAY_DEPLOYMENT_ID'),
                        "environment": os.environ.get('RAILWAY_ENVIRONMENT')
                    }
                }
            )

        @self.app.get("/metrics")
        @self.limiter.limit("10/minute")
        async def metrics(request: Request):
            """Basic metrics endpoint"""
            try:
                from rudeai_bot.database.base import get_db_context
                from rudeai_bot.database.operations import DatabaseOperations

                with get_db_context() as db:
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

    async def process_update(self, update: Update):
        """Process a Telegram update through the Application's handler system"""
        try:
            # Process the update through the Application's handler system
            # This allows ConversationHandler and other handlers to work properly
            await self.telegram_app.process_update(update)

        except Exception as e:
            logger.error(f"Error processing update {update.update_id}: {e}")
            if update.message:
                await update.message.reply_text(
                    "Something went wrong. Even I have limits, apparently."
                )

    async def _initialize_database_with_retry(self):
        """Initialize database with retry logic for Railway"""
        import asyncio
        from sqlalchemy import text

        max_retries = 5
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                from rudeai_bot.database.base import get_db_context
                with get_db_context() as db:
                    db.execute(text("SELECT 1"))
                logger.info("✅ Database connection established")

                # Create tables
                Base.metadata.create_all(bind=engine)
                logger.info("✅ Database tables created/verified")
                return

            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"⚠️ Database connection attempt {attempt + 1} failed: {e}")
                    logger.info(f"⏳ Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"❌ Database connection failed after {max_retries} attempts: {e}")
                    raise

    async def _initialize_database(self):
        """Initialize database for non-Railway environments"""
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("✅ Database tables created")
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise

    async def _initialize_ai_service(self):
        """Initialize AI service in background"""
        try:
            logger.info("🧠 Initializing AI service...")
            from rudeai_bot.services.ai_service import AIService
            self.ai_service = AIService()
            logger.info("✅ AI service initialized")
        except Exception as e:
            logger.error(f"❌ AI service initialization failed: {e}")
            self.ai_service = None

    async def _initialize_database_background(self):
        """Initialize database in background"""
        try:
            logger.info("🗄️ Connecting to database...")

            # Check Railway environment
            is_railway = os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('RAILWAY_PUBLIC_DOMAIN')

            if is_railway:
                await self._initialize_database_with_retry()
            else:
                await self._initialize_database()

        except Exception as e:
            logger.error(f"❌ Database background initialization failed: {e}")

    async def _initialize_telegram_app(self):
        """Initialize Telegram app in background"""
        try:
            logger.info("📱 Setting up Telegram...")
            self.telegram_app = self.setup_telegram_app()
            logger.info("✅ Telegram app configured")

            await self.telegram_app.initialize()
            logger.info("✅ Telegram app initialized")

            await self.telegram_app.start()
            logger.info("✅ Telegram app started")

            # Set up webhook
            await self.setup_webhook()
            logger.info("✅ Telegram webhook configured")

        except Exception as e:
            logger.error(f"❌ Telegram initialization failed: {e}")

    async def setup_webhook(self):
        """Set up the webhook with Telegram"""
        try:
            # Auto-detect deployment platform and construct webhook URL
            railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN')
            render_url = os.environ.get('RENDER_EXTERNAL_URL')

            if railway_domain:
                webhook_url = f"https://{railway_domain}/webhook/{settings.webhook_secret}"
                logger.info(f"🚂 Railway environment detected: {railway_domain}")
            elif render_url:
                webhook_url = f"{render_url}/webhook/{settings.webhook_secret}"
                logger.info(f"🎨 Render environment detected: {render_url}")
            else:
                webhook_url = f"{settings.webhook_url}/webhook/{settings.webhook_secret}"
                logger.info(f"💻 Using configured webhook URL: {settings.webhook_url}")

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
        """Initialize the webhook server - Railway optimized with detailed logging"""
        setup_logging()

        # RAILWAY DEBUG LOGGING
        logger.info("=" * 60)
        logger.info("🚂 RAILWAY DEPLOYMENT - DETAILED STARTUP LOG")
        logger.info("=" * 60)

        # Log ALL relevant environment variables
        logger.info("📋 ENVIRONMENT VARIABLES:")
        env_vars = {
            'PORT': os.environ.get('PORT'),
            'HOST': os.environ.get('HOST', '0.0.0.0'),
            'ENVIRONMENT': settings.environment,

            # Railway variables
            'RAILWAY_ENVIRONMENT': os.environ.get('RAILWAY_ENVIRONMENT'),
            'RAILWAY_PROJECT_ID': os.environ.get('RAILWAY_PROJECT_ID'),
            'RAILWAY_PUBLIC_DOMAIN': os.environ.get('RAILWAY_PUBLIC_DOMAIN'),

            # Render variables
            'RENDER_EXTERNAL_URL': os.environ.get('RENDER_EXTERNAL_URL'),
            'RENDER_SERVICE_NAME': os.environ.get('RENDER_SERVICE_NAME'),
            'RENDER_SERVICE_ID': os.environ.get('RENDER_SERVICE_ID'),
        }

        for key, value in env_vars.items():
            if value:
                logger.info(f"   ✅ {key}: {value}")
            else:
                logger.warning(f"   ❌ {key}: NOT SET")

        # Validate critical Railway requirements
        port = os.environ.get('PORT')
        if not port:
            logger.error("🚨 CRITICAL: PORT environment variable not set by Railway!")
            logger.error("   This will cause health check failures!")
        else:
            logger.info(f"✅ Railway PORT detected: {port}")

        # Log what the server will actually listen on
        actual_host = os.environ.get('HOST', '0.0.0.0')
        actual_port = int(port) if port else 8000
        logger.info(f"🔧 Server will bind to: {actual_host}:{actual_port}")

        try:
            logger.info("🚀 Starting background services...")
            logger.info("   (Health endpoint will be available immediately)")

            # Initialize services in background - don't block startup
            asyncio.create_task(self._initialize_ai_service())
            asyncio.create_task(self._initialize_database_background())
            asyncio.create_task(self._initialize_telegram_app())

            logger.info("✅ Background initialization started")
            logger.info("🎯 Health endpoint should be accessible at:")
            logger.info(f"   - http://{actual_host}:{actual_port}/health")
            logger.info(f"   - http://{actual_host}:{actual_port}/")

            if os.environ.get('RAILWAY_PUBLIC_DOMAIN'):
                domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN')
                logger.info(f"   - https://{domain}/health")
                logger.info(f"   - https://{domain}/")

            logger.info("🎉 Webhook server startup complete!")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"❌ Startup failed: {e}")
            logger.error("This may cause Railway health checks to fail")
            # Don't raise - allow server to start even if background tasks fail

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

    def setup_events(self):
        """Setup FastAPI event handlers for Railway debugging"""

        @self.app.on_event("startup")
        async def startup_event():
            logger.info("🚀 FASTAPI STARTUP EVENT TRIGGERED")
            logger.info("   Server is now accepting requests")
            logger.info(f"   Health endpoint: /health")
            logger.info(f"   Railway will check this endpoint")

            # Schedule background initialization
            await self.startup()

        @self.app.on_event("shutdown")
        async def shutdown_event():
            logger.info("🛑 FASTAPI SHUTDOWN EVENT TRIGGERED")
            await self.shutdown()


# Global server instance
webhook_server = WebhookServer()
app = webhook_server.get_app()