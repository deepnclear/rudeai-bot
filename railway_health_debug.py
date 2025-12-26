#!/usr/bin/env python3
"""
Railway Health Check Debug Script
This simulates Railway's health check process to identify issues
"""

import asyncio
import httpx
import os
import sys
from pathlib import Path
import time

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_railway_health_check_simulation():
    """Simulate Railway's health check process"""
    print("🚂 SIMULATING RAILWAY HEALTH CHECK")
    print("=" * 50)

    # Test different Railway domain patterns
    domains_to_test = [
        "localhost:8000",  # Local test
        "0.0.0.0:8000",    # Railway binding
    ]

    # Set Railway environment variables for testing
    os.environ["RAILWAY_ENVIRONMENT"] = "production"
    os.environ["PORT"] = "8000"
    os.environ["HOST"] = "0.0.0.0"

    print(f"📋 Environment Variables:")
    print(f"   PORT: {os.environ.get('PORT')}")
    print(f"   HOST: {os.environ.get('HOST')}")
    print(f"   RAILWAY_ENVIRONMENT: {os.environ.get('RAILWAY_ENVIRONMENT')}")

    for domain in domains_to_test:
        print(f"\n🔍 Testing domain: {domain}")

        endpoints = ["/health", "/", "/ping", "/status"]

        for endpoint in endpoints:
            url = f"http://{domain}{endpoint}"
            try:
                print(f"   📍 Testing: {url}")

                # Simulate Railway's health check request
                headers = {
                    "User-Agent": "Railway-HealthCheck/1.0",
                    "Host": "healthcheck.railway.app",
                    "Accept": "*/*",
                    "Connection": "close"
                }

                timeout = httpx.Timeout(30.0, connect=10.0)

                async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
                    start_time = time.time()
                    response = await client.get(url)
                    response_time = (time.time() - start_time) * 1000

                    print(f"      Status: {response.status_code}")
                    print(f"      Response time: {response_time:.2f}ms")
                    print(f"      Content-Type: {response.headers.get('content-type')}")

                    if response.status_code == 200:
                        print("      ✅ SUCCESS")
                        try:
                            data = response.json()
                            print(f"      Response: {data}")
                        except:
                            print(f"      Response (text): {response.text[:100]}...")
                    else:
                        print(f"      ❌ FAILED")
                        print(f"      Error: {response.text}")

            except httpx.ConnectError as e:
                print(f"      ❌ CONNECTION FAILED: {e}")
                print("         This is what Railway experiences!")

            except httpx.TimeoutException as e:
                print(f"      ❌ TIMEOUT: {e}")
                print("         Railway health check timed out!")

            except Exception as e:
                print(f"      ❌ ERROR: {e}")

async def test_port_binding():
    """Test if the app can bind to the PORT environment variable"""
    print("\n🔧 TESTING PORT BINDING")
    print("=" * 30)

    port = int(os.environ.get('PORT', '8000'))
    host = os.environ.get('HOST', '0.0.0.0')

    print(f"Testing if {host}:{port} is available...")

    try:
        import socket

        # Test if port is available
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()

        if result == 0:
            print(f"✅ Port {port} is accessible")
        else:
            print(f"❌ Port {port} is not accessible")
            print("   This could cause Railway health check failures")

    except Exception as e:
        print(f"❌ Port test failed: {e}")

def check_railway_requirements():
    """Check if all Railway requirements are met"""
    print("\n📋 RAILWAY REQUIREMENTS CHECK")
    print("=" * 35)

    requirements = [
        ("PORT environment variable", os.environ.get('PORT')),
        ("HOST environment variable", os.environ.get('HOST', '0.0.0.0')),
        ("Health endpoint exists", "Need to verify via HTTP"),
        ("App listens on PORT", "Need to verify via connection test"),
        ("Health check returns 200", "Need to verify via HTTP request")
    ]

    for req_name, status in requirements:
        if status and status != "Need to verify via HTTP" and status != "Need to verify via connection test":
            print(f"✅ {req_name}: {status}")
        elif status:
            print(f"⚠️  {req_name}: {status}")
        else:
            print(f"❌ {req_name}: NOT SET")

async def main():
    """Main debugging function"""
    print("🚂 RAILWAY HEALTH CHECK DEBUGGER")
    print("=" * 50)
    print("This simulates Railway's health check process")
    print("to identify why your deployment might be failing")
    print("")

    # Check requirements
    check_railway_requirements()

    # Test port binding
    await test_port_binding()

    # Test health endpoints
    await test_railway_health_check_simulation()

    print("\n📊 DEBUGGING SUMMARY")
    print("=" * 25)
    print("Common Railway health check failures:")
    print("1. App not listening on PORT environment variable")
    print("2. Health endpoint not returning 200 status code")
    print("3. Health endpoint taking too long to respond (>30s)")
    print("4. App crashing during startup before health check")
    print("5. Missing HOST=0.0.0.0 binding (app only listening on localhost)")
    print("")
    print("✅ If all tests pass locally, check Railway logs for:")
    print("   - PORT environment variable value")
    print("   - Startup errors")
    print("   - Health check request logs")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Debug script failed: {e}")
        sys.exit(1)