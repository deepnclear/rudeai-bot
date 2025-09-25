#!/usr/bin/env python3
"""
Quick health check for Railway deployment
Run this to test if your bot is accessible
"""

import asyncio
import httpx
import sys

async def check_health(domain):
    """Check health endpoint"""
    health_url = f"https://{domain}/health"

    print(f"🔍 Testing health endpoint: {health_url}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(health_url)

            if response.status_code == 200:
                data = response.json()
                print("✅ Health check passed!")
                print(f"   Status: {data.get('status')}")
                print(f"   Database: {data.get('database')}")
                print(f"   AI Service: {data.get('ai_service')}")
                print(f"   Environment: {data.get('environment')}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False

    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

async def check_root(domain):
    """Check root endpoint"""
    root_url = f"https://{domain}/"

    print(f"🔍 Testing root endpoint: {root_url}")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(root_url)

            if response.status_code == 200:
                data = response.json()
                print("✅ Root endpoint working!")
                print(f"   Service: {data.get('service')}")
                print(f"   Status: {data.get('status')}")
                return True
            else:
                print(f"❌ Root endpoint failed: {response.status_code}")
                return False

    except Exception as e:
        print(f"❌ Root endpoint error: {e}")
        return False

async def main():
    """Main health check"""
    if len(sys.argv) != 2:
        print("Usage: python health_check.py <your-railway-domain>")
        print("Example: python health_check.py rudeai-bot-production-abc123.up.railway.app")
        sys.exit(1)

    domain = sys.argv[1].replace('https://', '').replace('http://', '')

    print("🏥 RAILWAY HEALTH CHECK")
    print("=" * 40)
    print(f"Domain: {domain}")
    print()

    # Run checks
    root_ok = await check_root(domain)
    health_ok = await check_health(domain)

    print("\n📊 SUMMARY")
    print("=" * 20)

    if root_ok and health_ok:
        print("✅ All checks passed! Your bot is running correctly.")
        sys.exit(0)
    else:
        print("❌ Some checks failed. Check Railway logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())