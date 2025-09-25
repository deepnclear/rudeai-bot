#!/usr/bin/env python3
"""
Railway Deployment Debug Script
Run this to check all components systematically
"""

import os
import asyncio
import httpx
from rudeai_bot.config.settings import settings
from rudeai_bot.database.base import get_db, engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_environment():
    """Check environment variables"""
    print("🔧 ENVIRONMENT VARIABLES")
    print("=" * 40)

    required_vars = [
        'OPENAI_API_KEY',
        'TELEGRAM_BOT_TOKEN',
        'WEBHOOK_SECRET',
        'DATABASE_URL',
        'PORT'
    ]

    missing_vars = []
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            # Mask sensitive values
            if 'KEY' in var or 'TOKEN' in var:
                display_value = f"{value[:10]}...{value[-4:]}" if len(value) > 14 else "***"
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: Missing!")
            missing_vars.append(var)

    print(f"\n🌍 Railway Environment: {os.environ.get('RAILWAY_ENVIRONMENT', 'Not detected')}")
    print(f"🌐 Railway Domain: {os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'Not assigned')}")

    return len(missing_vars) == 0

async def debug_database():
    """Test database connection"""
    print("\n🗄️  DATABASE CONNECTION")
    print("=" * 40)

    try:
        # Test basic connection
        with next(get_db()) as db:
            result = db.execute(text("SELECT 1 as test")).scalar()
            print(f"✅ Database connection: Working (result: {result})")

            # Check if tables exist
            tables_query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            """
            tables = db.execute(text(tables_query)).fetchall()
            print(f"✅ Database tables: {len(tables)} found")
            for table in tables:
                print(f"   - {table[0]}")

        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print(f"   Database URL: {os.environ.get('DATABASE_URL', 'Not set')[:50]}...")
        return False

async def debug_webhook():
    """Test webhook setup"""
    print("\n🔗 WEBHOOK CONFIGURATION")
    print("=" * 40)

    try:
        # Check webhook URL construction
        railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN')
        if railway_domain:
            webhook_url = f"https://{railway_domain}/webhook/{settings.webhook_secret}"
            print(f"✅ Railway domain detected: {railway_domain}")
            print(f"✅ Webhook URL: {webhook_url}")
        else:
            webhook_url = f"{settings.webhook_url}/webhook/{settings.webhook_secret}"
            print(f"⚠️  Using fallback webhook URL: {webhook_url}")

        # Test webhook endpoint accessibility
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(webhook_url.replace('/webhook/', '/health'))
                print(f"✅ Health endpoint accessible: {response.status_code}")
        except Exception as e:
            print(f"❌ Webhook endpoint not accessible: {e}")

        # Check Telegram webhook status
        telegram_url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/getWebhookInfo"
        async with httpx.AsyncClient() as client:
            response = await client.get(telegram_url)
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    webhook_info = data.get("result", {})
                    print(f"✅ Telegram webhook URL: {webhook_info.get('url', 'Not set')}")
                    print(f"✅ Pending updates: {webhook_info.get('pending_update_count', 0)}")
                    last_error = webhook_info.get('last_error_message')
                    if last_error:
                        print(f"⚠️  Last error: {last_error}")
                    else:
                        print("✅ No webhook errors")
                else:
                    print(f"❌ Telegram API error: {data.get('description')}")
            else:
                print(f"❌ Failed to check webhook: {response.status_code}")

        return True
    except Exception as e:
        print(f"❌ Webhook debug failed: {e}")
        return False

async def debug_openai():
    """Test OpenAI connection"""
    print("\n🤖 OPENAI CONNECTION")
    print("=" * 40)

    try:
        from rudeai_bot.services.ai_service import AIService
        ai_service = AIService()

        # Test a simple completion
        response = await ai_service.get_response("Test", 5, 0, [])
        print(f"✅ OpenAI API: Working")
        print(f"✅ Test response: {response[:50]}...")
        await ai_service.close()
        return True
    except Exception as e:
        print(f"❌ OpenAI connection failed: {e}")
        return False

async def debug_server():
    """Test server startup"""
    print("\n🚀 SERVER STARTUP")
    print("=" * 40)

    try:
        from rudeai_bot.webhook_server import WebhookServer

        # Test server initialization
        server = WebhookServer()
        print("✅ WebhookServer initialized")

        # Test FastAPI app
        app = server.get_app()
        print("✅ FastAPI app created")

        return True
    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        return False

async def main():
    """Run all debug checks"""
    print("🔍 RAILWAY DEPLOYMENT DEBUG")
    print("=" * 50)

    results = {}

    # Run all checks
    results['environment'] = await debug_environment()
    results['database'] = await debug_database()
    results['webhook'] = await debug_webhook()
    results['openai'] = await debug_openai()
    results['server'] = await debug_server()

    # Summary
    print("\n📊 DEBUG SUMMARY")
    print("=" * 40)

    passed = sum(results.values())
    total = len(results)

    for check, passed_check in results.items():
        status = "✅ PASS" if passed_check else "❌ FAIL"
        print(f"{check.upper()}: {status}")

    print(f"\n🎯 Overall: {passed}/{total} checks passed")

    if passed == total:
        print("✅ All checks passed! Your deployment should be working.")
    else:
        print("❌ Some checks failed. Fix the issues above and redeploy.")

if __name__ == "__main__":
    asyncio.run(main())