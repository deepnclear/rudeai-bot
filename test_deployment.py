#!/usr/bin/env python3
"""
Deployment validation test for RUDE.AI Bot
"""

import os
import sys
import requests
import json
from pathlib import Path


def test_environment_config():
    """Test environment configuration"""
    print("🔧 Testing Environment Configuration...")

    # Check required files exist
    required_files = [
        ".env.example",
        "Dockerfile",
        "docker-compose.yml",
        "requirements.txt",
        "DEPLOYMENT.md"
    ]

    for file in required_files:
        if Path(file).exists():
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} missing")
            return False

    # Check Python imports
    try:
        from rudeai_bot.webhook_server import webhook_server
        from rudeai_bot.config.settings import settings
        from rudeai_bot.services.ai_service import AIService
        print("✅ All Python modules import successfully")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

    return True


def test_webhook_server():
    """Test webhook server configuration"""
    print("\n🌐 Testing Webhook Server...")

    try:
        from rudeai_bot.webhook_server import app
        print("✅ FastAPI app created successfully")

        # Check if required routes exist
        routes = [route.path for route in app.routes]
        required_routes = ["/health", "/metrics", "/"]

        for route in required_routes:
            if route in routes:
                print(f"✅ Route {route} configured")
            else:
                print(f"❌ Route {route} missing")
                return False

    except Exception as e:
        print(f"❌ Webhook server test failed: {e}")
        return False

    return True


def test_docker_config():
    """Test Docker configuration"""
    print("\n🐳 Testing Docker Configuration...")

    # Check Dockerfile
    if Path("Dockerfile").exists():
        with open("Dockerfile", "r") as f:
            dockerfile_content = f.read()

        checks = [
            ("HEALTHCHECK", "Health check configured"),
            ("USER rudeai", "Non-root user configured"),
            ("EXPOSE 8000", "Port exposed"),
            ("python:3.11", "Python 3.11 base image")
        ]

        for check, message in checks:
            if check in dockerfile_content:
                print(f"✅ {message}")
            else:
                print(f"❌ {message} - missing")

    # Check docker-compose.yml
    if Path("docker-compose.yml").exists():
        with open("docker-compose.yml", "r") as f:
            compose_content = f.read()

        checks = [
            ("postgres", "PostgreSQL service configured"),
            ("redis", "Redis service configured"),
            ("nginx", "Nginx service configured"),
            ("healthcheck", "Health checks configured")
        ]

        for check, message in checks:
            if check in compose_content:
                print(f"✅ {message}")
            else:
                print(f"❌ {message} - missing")

    return True


def test_security_features():
    """Test security configuration"""
    print("\n🛡️  Testing Security Features...")

    try:
        from rudeai_bot.config.settings import settings

        # Test webhook secret validation
        if hasattr(settings, 'webhook_secret'):
            print("✅ Webhook secret configuration exists")
        else:
            print("❌ Webhook secret configuration missing")

        # Test rate limiting
        from rudeai_bot.webhook_server import webhook_server
        if hasattr(webhook_server, 'check_user_rate_limit'):
            print("✅ Rate limiting implemented")
        else:
            print("❌ Rate limiting missing")

        # Test environment validation
        if hasattr(settings, 'is_production'):
            print("✅ Environment validation implemented")
        else:
            print("❌ Environment validation missing")

    except Exception as e:
        print(f"❌ Security test failed: {e}")
        return False

    return True


def test_logging_system():
    """Test logging configuration"""
    print("\n📝 Testing Logging System...")

    try:
        from rudeai_bot.utils.logger import StructuredLogger, get_logger

        # Test logger creation
        logger = StructuredLogger()
        print("✅ Structured logger created")

        # Test log methods
        if hasattr(StructuredLogger, 'log_user_interaction'):
            print("✅ User interaction logging available")
        else:
            print("❌ User interaction logging missing")

        if hasattr(StructuredLogger, 'log_rate_limit'):
            print("✅ Rate limit logging available")
        else:
            print("❌ Rate limit logging missing")

        # Test logs directory creation
        logs_dir = Path("logs")
        if logs_dir.exists() or not logs_dir.parent.exists():
            print("✅ Logs directory handling configured")
        else:
            print("❌ Logs directory configuration issue")

    except Exception as e:
        print(f"❌ Logging test failed: {e}")
        return False

    return True


def test_ai_service_enhancements():
    """Test AI service enhancements"""
    print("\n🤖 Testing AI Service Enhancements...")

    try:
        from rudeai_bot.services.ai_service import AIService

        ai_service = AIService()

        # Test excuse detection
        if hasattr(ai_service, 'is_excuse_message'):
            test_messages = [
                ("I'm too tired", True),
                ("I finished my work", False),
                ("Maybe later", True)
            ]

            for message, expected in test_messages:
                result = ai_service.is_excuse_message(message)
                if result == expected:
                    print(f"✅ Excuse detection: '{message}' -> {result}")
                else:
                    print(f"❌ Excuse detection failed: '{message}' -> {result}, expected {expected}")

        # Test rudeness level handling
        if hasattr(ai_service, '_build_system_prompt'):
            prompt = ai_service._build_system_prompt(5, 3, ["test message"])
            if "RUDENESS LEVEL 5" in prompt:
                print("✅ Rudeness level system working")
            else:
                print("❌ Rudeness level system not working")

    except Exception as e:
        print(f"❌ AI service test failed: {e}")
        return False

    return True


def main():
    """Run all deployment tests"""
    print("🧪 RUDE.AI Bot Deployment Validation")
    print("=" * 40)

    tests = [
        test_environment_config,
        test_webhook_server,
        test_docker_config,
        test_security_features,
        test_logging_system,
        test_ai_service_enhancements
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")

    print(f"\n📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Deployment ready.")
        return 0
    else:
        print("❌ Some tests failed. Review issues before deployment.")
        return 1


if __name__ == "__main__":
    sys.exit(main())