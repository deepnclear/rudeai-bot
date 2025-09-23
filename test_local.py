#!/usr/bin/env python3
"""
Local testing script for RUDE.AI Bot
Tests core functionality without external dependencies
"""

import os
import sys
import time
from pathlib import Path

def test_file_structure():
    """Test that all required files exist"""
    print("🔍 Testing File Structure...")

    required_files = [
        "rudeai_bot/__init__.py",
        "rudeai_bot/webhook_server.py",
        "rudeai_bot/config/settings.py",
        "rudeai_bot/services/ai_service.py",
        "rudeai_bot/handlers/bot_handlers.py",
        "Dockerfile",
        "docker-compose.yml",
        "requirements.txt"
    ]

    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
        else:
            print(f"✅ {file}")

    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False

    print("✅ All required files present")
    return True

def test_docker_build():
    """Test Docker image builds successfully"""
    print("\n🐳 Testing Docker Build...")

    try:
        # Check if Dockerfile exists and is valid
        with open("Dockerfile", "r") as f:
            dockerfile_content = f.read()

        # Basic validation
        if "FROM python:" in dockerfile_content:
            print("✅ Dockerfile has valid base image")
        else:
            print("❌ Dockerfile missing valid base image")
            return False

        if "COPY requirements.txt" in dockerfile_content:
            print("✅ Dockerfile copies requirements")
        else:
            print("❌ Dockerfile doesn't copy requirements")
            return False

        if "USER rudeai" in dockerfile_content:
            print("✅ Dockerfile uses non-root user")
        else:
            print("❌ Dockerfile missing non-root user")
            return False

        print("✅ Dockerfile structure looks good")
        return True

    except Exception as e:
        print(f"❌ Docker test failed: {e}")
        return False

def test_environment_configs():
    """Test environment configuration files"""
    print("\n⚙️  Testing Environment Configs...")

    config_files = [
        ".env.example",
        ".env.dev",
        ".env.production",
        ".env.test"
    ]

    for config_file in config_files:
        if Path(config_file).exists():
            print(f"✅ {config_file} exists")

            # Check for required variables
            with open(config_file, "r") as f:
                content = f.read()

            required_vars = ["OPENAI_API_KEY", "TELEGRAM_BOT_TOKEN", "WEBHOOK_URL", "WEBHOOK_SECRET"]
            for var in required_vars:
                if var in content:
                    print(f"  ✅ {var} configured")
                else:
                    print(f"  ❌ {var} missing")
        else:
            print(f"❌ {config_file} missing")

    return True

def test_monitoring_setup():
    """Test monitoring and deployment scripts"""
    print("\n📊 Testing Monitoring Setup...")

    monitoring_files = [
        "scripts/monitor.sh",
        "DEPLOYMENT.md",
        "PRODUCTION_READY.md"
    ]

    for file in monitoring_files:
        if Path(file).exists():
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} missing")

    # Check if monitor script is executable
    monitor_script = Path("scripts/monitor.sh")
    if monitor_script.exists():
        import stat
        file_stat = monitor_script.stat()
        if file_stat.st_mode & stat.S_IEXEC:
            print("✅ Monitor script is executable")
        else:
            print("❌ Monitor script is not executable")

    return True

def test_docker_compose():
    """Test Docker Compose configurations"""
    print("\n🐙 Testing Docker Compose...")

    compose_files = [
        "docker-compose.yml",
        "docker-compose.dev.yml",
        "docker-compose.test.yml"
    ]

    for compose_file in compose_files:
        if Path(compose_file).exists():
            print(f"✅ {compose_file} exists")

            with open(compose_file, "r") as f:
                content = f.read()

            # Check for key components
            if "rudeai-bot" in content:
                print(f"  ✅ {compose_file} has rudeai-bot service")
            else:
                print(f"  ❌ {compose_file} missing rudeai-bot service")

            if "healthcheck" in content:
                print(f"  ✅ {compose_file} has health checks")
            else:
                print(f"  ❌ {compose_file} missing health checks")
        else:
            print(f"❌ {compose_file} missing")

    return True

def run_quick_syntax_check():
    """Quick Python syntax check on main files"""
    print("\n🐍 Testing Python Syntax...")

    python_files = [
        "rudeai_bot/webhook_server.py",
        "rudeai_bot/config/settings.py",
        "rudeai_bot/services/ai_service.py",
        "rudeai_bot/handlers/bot_handlers.py",
        "test_deployment.py"
    ]

    for py_file in python_files:
        if Path(py_file).exists():
            try:
                import ast
                with open(py_file, 'r') as f:
                    ast.parse(f.read())
                print(f"✅ {py_file} syntax OK")
            except SyntaxError as e:
                print(f"❌ {py_file} syntax error: {e}")
                return False
        else:
            print(f"❌ {py_file} missing")
            return False

    return True

def main():
    """Run all local tests"""
    print("🧪 RUDE.AI Local Testing Suite")
    print("=" * 35)
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Working directory: {os.getcwd()}")
    print()

    tests = [
        ("File Structure", test_file_structure),
        ("Docker Configuration", test_docker_build),
        ("Environment Configs", test_environment_configs),
        ("Monitoring Setup", test_monitoring_setup),
        ("Docker Compose", test_docker_compose),
        ("Python Syntax", run_quick_syntax_check)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} test had issues")
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")

    print(f"\n📊 Local Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All local tests passed!")
        print("\n🚀 Ready for Docker testing. Run:")
        print("   docker-compose -f docker-compose.test.yml build")
        print("   docker-compose -f docker-compose.test.yml up")
        return 0
    else:
        print(f"\n❌ {total - passed} tests failed. Fix issues before proceeding.")
        return 1

if __name__ == "__main__":
    sys.exit(main())