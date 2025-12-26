#!/usr/bin/env python3
"""
Railway-specific startup script for RUDE.AI bot
Handles Railway environment detection and graceful startup
"""

import os
import sys
import asyncio
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import uvicorn
from loguru import logger

def setup_railway_environment():
    """Setup Railway-specific environment variables"""

    # Set Railway-specific flags
    os.environ["RAILWAY_ENVIRONMENT"] = "production"

    # Ensure required environment variables
    required_vars = [
        "OPENAI_API_KEY",
        "TELEGRAM_BOT_TOKEN",
        "WEBHOOK_SECRET",
        "DATABASE_URL"
    ]

    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)

    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {missing_vars}")
        logger.error("Set these in Railway dashboard → Variables")
        sys.exit(1)

    # Set Railway defaults
    if not os.environ.get("PORT"):
        os.environ["PORT"] = "8000"

    if not os.environ.get("HOST"):
        os.environ["HOST"] = "0.0.0.0"

    # Set webhook URL from Railway domain if available
    railway_domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN")
    if railway_domain and not os.environ.get("WEBHOOK_URL"):
        os.environ["WEBHOOK_URL"] = f"https://{railway_domain}"

    logger.info("✅ Railway environment configured")

async def wait_for_services():
    """Wait for external services to be ready"""
    logger.info("⏳ Waiting for services to be ready...")

    # Give Railway time to set up networking
    await asyncio.sleep(5)

    # Test database connection
    max_retries = 10
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            from rudeai_bot.database.base import get_db
            from sqlalchemy import text

            with next(get_db()) as db:
                db.execute(text("SELECT 1"))
            logger.info("✅ Database ready")
            break

        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"⚠️ Database not ready (attempt {attempt + 1}): {e}")
                await asyncio.sleep(retry_delay)
            else:
                logger.error(f"❌ Database failed to start: {e}")
                raise

def main():
    """Main startup function for Railway"""
    logger.info("🚂 Starting RUDE.AI on Railway...")

    # Setup environment
    setup_railway_environment()

    # Wait for services
    asyncio.run(wait_for_services())

    # Get configuration
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))

    logger.info(f"🚀 Starting server on {host}:{port}")

    # Start uvicorn with Railway-optimized settings
    uvicorn.run(
        "rudeai_bot.webhook_server:app",
        host=host,
        port=port,
        timeout_keep_alive=30,
        access_log=True,
        log_level="info",
        reload=False,
        workers=1,
        loop="asyncio"
    )

if __name__ == "__main__":
    main()