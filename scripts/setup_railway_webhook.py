#!/usr/bin/env python3
"""
Railway webhook setup script
Automatically configures Telegram webhook URL when deployed
"""

import os
import httpx
import asyncio
from rudeai_bot.config.settings import settings


async def setup_telegram_webhook():
    """Set up Telegram webhook automatically on Railway"""

    # Get Railway-provided URL
    railway_url = os.environ.get('RAILWAY_PUBLIC_DOMAIN')
    if railway_url:
        webhook_url = f"https://{railway_url}/webhook/{settings.webhook_secret}"
    else:
        # Fallback to webhook_url from settings
        webhook_url = f"{settings.webhook_url}/webhook/{settings.webhook_secret}"

    print(f"Setting up webhook URL: {webhook_url}")

    # Set up webhook with Telegram
    telegram_url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/setWebhook"

    payload = {
        "url": webhook_url,
        "allowed_updates": ["message", "callback_query"],
        "drop_pending_updates": True
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(telegram_url, json=payload)

        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                print("✅ Webhook set up successfully!")
                print(f"Webhook URL: {webhook_url}")
                return True
            else:
                print(f"❌ Telegram API error: {data.get('description', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error setting up webhook: {e}")
        return False


async def check_webhook_status():
    """Check current webhook status"""
    telegram_url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/getWebhookInfo"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(telegram_url)

        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                webhook_info = data.get("result", {})
                print("📊 Current webhook status:")
                print(f"  URL: {webhook_info.get('url', 'Not set')}")
                print(f"  Pending updates: {webhook_info.get('pending_update_count', 0)}")
                print(f"  Last error: {webhook_info.get('last_error_message', 'None')}")
                return webhook_info
            else:
                print(f"❌ Telegram API error: {data.get('description', 'Unknown error')}")
                return None
        else:
            print(f"❌ HTTP error: {response.status_code}")
            return None

    except Exception as e:
        print(f"❌ Error checking webhook: {e}")
        return None


async def main():
    """Main setup function"""
    print("🚀 Railway Webhook Setup for RUDE.AI Bot")
    print("=" * 40)

    # Check current status
    webhook_info = await check_webhook_status()

    # Set up webhook
    if await setup_telegram_webhook():
        print("\n✅ Webhook setup completed successfully!")

        # Verify the setup
        print("\n🔍 Verifying webhook setup...")
        await check_webhook_status()
    else:
        print("\n❌ Webhook setup failed!")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())