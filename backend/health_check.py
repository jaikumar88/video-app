#!/usr/bin/env python3
"""
System Health Check Script
Validates core application components and dependencies.
"""

import asyncio
import sys
import importlib
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

async def test_imports():
    """Test critical imports."""
    print("🔍 Testing imports...")
    
    try:
        # Test core imports
        from app.core.config import get_settings
        from app.core.database import initialize_database, create_tables
        print("✅ Core modules imported successfully")
        
        # Test API imports
        from app.api.auth import router as auth_router
        from app.api.meetings import router as meetings_router
        print("✅ API modules imported successfully")
        
        # Test service imports
        from app.services.auth_service import AuthService
        from app.services.email_service import EmailService
        print("✅ Service modules imported successfully")
        
        # Test model imports
        from app.models.user import User
        from app.models.meeting import Meeting
        print("✅ Model modules imported successfully")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False


async def test_configuration():
    """Test configuration."""
    print("\n🔧 Testing configuration...")
    
    try:
        from app.core.config import get_settings
        settings = get_settings()
        
        print(f"✅ Environment: {settings.ENVIRONMENT}")
        print(f"✅ Database URL: {settings.DATABASE_URL}")
        print(f"✅ Debug mode: {settings.DEBUG}")
        
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False


async def test_database_initialization():
    """Test database initialization."""
    print("\n🗄️  Testing database initialization...")
    
    try:
        from app.core.database import initialize_database
        initialize_database()
        print("✅ Database engine initialized")
        
        return True
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        return False


async def test_app_creation():
    """Test FastAPI app creation."""
    print("\n🚀 Testing application creation...")
    
    try:
        from main import create_app
        app = create_app()
        
        print(f"✅ FastAPI app created: {app.title}")
        print(f"✅ Version: {app.version}")
        
        return True
    except Exception as e:
        print(f"❌ App creation error: {e}")
        return False


async def main():
    """Run all health checks."""
    print("🎯 WorldClass Video Platform - System Health Check")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_configuration,
        test_database_initialization,
        test_app_creation
    ]
    
    results = []
    for test in tests:
        result = await test()
        results.append(result)
    
    print("\n" + "=" * 50)
    print("📊 Health Check Summary:")
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if all(results):
        print("\n🎉 All health checks passed! System is ready.")
        return 0
    else:
        print("\n⚠️  Some health checks failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)