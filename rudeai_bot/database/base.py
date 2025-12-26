import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from rudeai_bot.config.settings import settings

# Railway-optimized database configuration
def get_engine():
    """Create database engine with Railway-optimized settings"""
    if "sqlite" in settings.database_url:
        # SQLite for local development
        return create_engine(
            settings.database_url,
            echo=settings.debug,
            connect_args={"check_same_thread": False}
        )
    else:
        # PostgreSQL for Railway/Render production
        app_name = "rudeai_bot"
        if os.environ.get('RENDER_SERVICE_NAME'):
            app_name = f"rudeai_bot_{os.environ.get('RENDER_SERVICE_NAME')}"
        elif os.environ.get('RAILWAY_DEPLOYMENT_ID'):
            app_name = f"rudeai_bot_{os.environ.get('RAILWAY_DEPLOYMENT_ID')[:8]}"

        return create_engine(
            settings.database_url,
            echo=settings.debug,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=3600,
            pool_pre_ping=True,  # Validates connections before use
            connect_args={
                "connect_timeout": 30,
                "application_name": app_name
            }
        )

engine = get_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """Context manager for database sessions - use this for non-FastAPI code"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()