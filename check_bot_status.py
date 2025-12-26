#!/usr/bin/env python3
"""
Quick bot status checker - run this to diagnose issues
"""

import asyncio
import httpx
import os

async def check_telegram_bot_info():
    """Check if your Telegram bot token is working"""
    print("🤖 CHECKING TELEGRAM BOT")
    print("=" * 30)

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN not set in environment")
        return False

    try:
        async with httpx.AsyncClient() as client:
            # Check bot info
            response = await client.get(f"https://api.telegram.org/bot{token}/getMe")
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    bot_info = data["result"]
                    print(f"✅ Bot token valid")
                    print(f"   Username: @{bot_info.get('username')}")
                    print(f"   Name: {bot_info.get('first_name')}")
                    print(f"   ID: {bot_info.get('id')}")
                else:
                    print(f"❌ Bot API error: {data.get('description')}")
                    return False
            else:
                print(f"❌ HTTP error: {response.status_code}")
                return False

            # Check webhook status
            response = await client.get(f"https://api.telegram.org/bot{token}/getWebhookInfo")
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    webhook_info = data["result"]
                    webhook_url = webhook_info.get("url", "")
                    if webhook_url:
                        print(f"✅ Webhook set to: {webhook_url}")
                        pending = webhook_info.get("pending_update_count", 0)
                        if pending > 0:
                            print(f"⚠️  Pending messages: {pending}")
                        else:
                            print("✅ No pending messages")

                        last_error = webhook_info.get("last_error_message")
                        if last_error:
                            print(f"❌ Last error: {last_error}")
                            return False
                    else:
                        print("❌ No webhook configured")
                        return False
                else:
                    print(f"❌ Webhook check failed: {data.get('description')}")
                    return False

        return True
    except Exception as e:
        print(f"❌ Error checking bot: {e}")
        return False

async def check_openai_key():
    """Check if OpenAI key is working"""
    print("\n🧠 CHECKING OPENAI API")
    print("=" * 30)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set in environment")
        return False

    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get("https://api.openai.com/v1/models", headers=headers)

            if response.status_code == 200:
                print("✅ OpenAI API key valid")
                data = response.json()
                models = [model["id"] for model in data["data"] if "gpt-4" in model["id"]]
                print(f"   Available models: {len(models)} GPT-4 variants found")
                return True
            else:
                print(f"❌ OpenAI API error: {response.status_code}")
                print(f"   Response: {response.text}")
                return False

    except Exception as e:
        print(f"❌ Error checking OpenAI: {e}")
        return False

async def check_railway_domain():
    """Try to guess and check Railway domain"""
    print("\n🚂 CHECKING RAILWAY DEPLOYMENT")
    print("=" * 30)

    # Common Railway domain patterns
    possible_domains = [
        "rudeai-bot-production.up.railway.app",
        "deepnclear-rudeai-bot-production.up.railway.app",
        "rudeai-bot.up.railway.app"
    ]

    for domain in possible_domains:
        print(f"🔍 Trying: https://{domain}")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"https://{domain}/health")
                if response.status_code == 200:
                    print(f"✅ Found working domain: {domain}")
                    data = response.json()
                    print(f"   Status: {data.get('status')}")
                    print(f"   Database: {data.get('database')}")
                    return domain
                else:
                    print(f"   Status: {response.status_code}")
        except Exception as e:
            print(f"   Error: Connection failed")

    print("❌ Could not find working Railway domain")
    print("   Check Railway Dashboard → Settings → Domains")
    return None

async def main():
    """Run all checks"""
    print("🔍 BOT STATUS DIAGNOSTIC")
    print("=" * 50)

    # Check components
    telegram_ok = await check_telegram_bot_info()
    openai_ok = await check_openai_key()
    railway_domain = await check_railway_domain()

    print("\n📊 DIAGNOSTIC SUMMARY")
    print("=" * 30)
    print(f"Telegram Bot: {'✅ Working' if telegram_ok else '❌ Issues'}")
    print(f"OpenAI API: {'✅ Working' if openai_ok else '❌ Issues'}")
    print(f"Railway App: {'✅ Working' if railway_domain else '❌ Not accessible'}")

    if telegram_ok and openai_ok and railway_domain:
        print("\n🎉 All systems working! Bot should be operational.")
        print(f"\nTry messaging your bot: @{await get_bot_username()}")
    else:
        print(f"\n🚨 Issues detected. Check the failures above.")
        print("\nNext steps:")
        if not telegram_ok:
            print("- Check Telegram bot token in Railway environment variables")
        if not openai_ok:
            print("- Check OpenAI API key in Railway environment variables")
        if not railway_domain:
            print("- Check Railway deployment status and logs")

async def get_bot_username():
    """Get bot username"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        return None
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://api.telegram.org/bot{token}/getMe")
            if response.status_code == 200:
                data = response.json()
                return data["result"]["username"]
    except:
        pass
    return "your_bot"

if __name__ == "__main__":
    asyncio.run(main())