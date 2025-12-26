#!/usr/bin/env python3
"""
Railway Health Check Debugger
Run this to test the health endpoint locally before deployment
"""

import asyncio
import httpx
import uvicorn
import multiprocessing
import time
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_local_health_endpoint():
    """Test the health endpoint locally"""
    print("🔍 Testing local health endpoint...")

    # Test different endpoints
    endpoints = [
        "http://localhost:8000/health",
        "http://localhost:8000/",
        "http://0.0.0.0:8000/health",
        "http://0.0.0.0:8000/"
    ]

    for endpoint in endpoints:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                print(f"\n📍 Testing: {endpoint}")
                response = await client.get(endpoint)

                print(f"   Status: {response.status_code}")
                print(f"   Headers: {dict(response.headers)}")

                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"   Response: {data}")
                        print("   ✅ SUCCESS")
                    except Exception as e:
                        print(f"   Response (text): {response.text}")
                        print("   ✅ SUCCESS (non-JSON)")
                else:
                    print(f"   ❌ FAILED: {response.status_code}")
                    print(f"   Error: {response.text}")

        except Exception as e:
            print(f"   ❌ CONNECTION FAILED: {e}")

def run_server():
    """Run the server in a subprocess"""
    import os
    os.environ.setdefault("ENVIRONMENT", "development")
    os.environ.setdefault("OPENAI_API_KEY", "test-key")
    os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
    os.environ.setdefault("WEBHOOK_SECRET", "test-webhook-secret-12345")
    os.environ.setdefault("WEBHOOK_URL", "http://localhost:8000")
    os.environ.setdefault("DATABASE_URL", "sqlite:///test.db")

    try:
        uvicorn.run(
            "rudeai_bot.webhook_server:app",
            host="0.0.0.0",
            port=8000,
            log_level="info",
            reload=False
        )
    except Exception as e:
        print(f"Server failed: {e}")

async def main():
    """Main debugging function"""
    print("🚂 RAILWAY HEALTH CHECK DEBUGGER")
    print("=" * 50)

    print("\n1️⃣ Starting local server...")

    # Start server in background process
    server_process = multiprocessing.Process(target=run_server)
    server_process.start()

    # Wait for server to start
    print("⏳ Waiting for server to start...")
    await asyncio.sleep(5)

    try:
        print("\n2️⃣ Testing health endpoints...")
        await test_local_health_endpoint()

        print("\n3️⃣ Testing Railway-specific scenarios...")

        # Test with Railway environment variables
        import os
        original_env = os.environ.copy()

        try:
            os.environ["RAILWAY_ENVIRONMENT"] = "production"
            os.environ["RAILWAY_PUBLIC_DOMAIN"] = "test-domain.up.railway.app"
            os.environ["PORT"] = "8000"

            print("✅ Railway environment variables set")
            print(f"   RAILWAY_ENVIRONMENT: {os.environ.get('RAILWAY_ENVIRONMENT')}")
            print(f"   RAILWAY_PUBLIC_DOMAIN: {os.environ.get('RAILWAY_PUBLIC_DOMAIN')}")
            print(f"   PORT: {os.environ.get('PORT')}")

        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)

        print("\n4️⃣ Final health check...")
        await test_local_health_endpoint()

    except Exception as e:
        print(f"❌ Test failed: {e}")

    finally:
        print("\n🛑 Stopping server...")
        server_process.terminate()
        server_process.join(timeout=5)

        if server_process.is_alive():
            print("⚠️ Server didn't stop gracefully, killing...")
            server_process.kill()
            server_process.join()

        print("✅ Server stopped")

    print("\n📋 DEBUGGING SUMMARY")
    print("=" * 30)
    print("If health checks failed:")
    print("1. Check that the server starts without errors")
    print("2. Ensure /health endpoint returns 200 status")
    print("3. Verify environment variables are set correctly")
    print("4. Check Railway logs for specific errors")
    print("5. Make sure Railway domain is accessible")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Debug script failed: {e}")
        sys.exit(1)