"""
Database configuration and session management.

This module handles database connections, session management,
and provides utilities for database operations.
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import logging
from typing import Generator

from .models import Base

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://dprofiler:password@localhost:5432/dprofiler"
)

# Engine configuration
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true"
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """Create all database tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


def drop_tables():
    """Drop all database tables."""
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("Database tables dropped successfully")
    except Exception as e:
        logger.error(f"Error dropping database tables: {e}")
        raise


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for database sessions."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """Dependency function for FastAPI."""
    with get_db_session() as session:
        yield session


class DatabaseManager:
    """Database manager for handling connections and operations."""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    def init_db(self):
        """Initialize the database."""
        create_tables()
        logger.info("Database initialized successfully")
    
    def reset_db(self):
        """Reset the database (drop and recreate tables)."""
        drop_tables()
        create_tables()
        logger.info("Database reset successfully")
    
    def check_connection(self) -> bool:
        """Check if database connection is working."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            return False
    
    def get_connection_info(self) -> dict:
        """Get database connection information."""
        return {
            "url": str(self.engine.url),
            "pool_size": self.engine.pool.size(),
            "checked_in": self.engine.pool.checkedin(),
            "checked_out": self.engine.pool.checkedout(),
            "overflow": self.engine.pool.overflow(),
        }


# Global database manager instance
db_manager = DatabaseManager()


def health_check() -> dict:
    """Perform database health check."""
    try:
        connection_ok = db_manager.check_connection()
        connection_info = db_manager.get_connection_info()
        
        return {
            "status": "healthy" if connection_ok else "unhealthy",
            "database": {
                "connected": connection_ok,
                "connection_info": connection_info
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        } 