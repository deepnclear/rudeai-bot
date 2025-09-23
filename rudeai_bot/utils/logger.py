import sys
import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from loguru import logger
from rudeai_bot.config.settings import settings


class StructuredLogger:
    """Enhanced logger with structured logging for production"""

    def __init__(self):
        self.setup_logging()

    def setup_logging(self):
        """Setup logging configuration based on environment"""
        logger.remove()

        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # Base format for development
        if settings.is_development:
            log_format = (
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                "<level>{message}</level>"
            )
        else:
            # JSON format for production
            log_format = self._json_formatter

        # Console logging
        logger.add(
            sys.stderr,
            format=log_format,
            level=settings.log_level,
            colorize=settings.is_development,
            backtrace=settings.debug,
            diagnose=settings.debug
        )

        # File logging
        if settings.log_file or not settings.is_development:
            log_file = settings.log_file or "logs/rudeai.log"
            logger.add(
                log_file,
                format=log_format,
                level=settings.log_level,
                rotation="100 MB",
                retention=settings.log_retention,
                compression="zip",
                enqueue=True  # Thread-safe logging
            )

        # Error logging (separate file)
        logger.add(
            "logs/errors.log",
            format=log_format,
            level="ERROR",
            rotation="50 MB",
            retention="90 days",
            compression="zip",
            enqueue=True
        )

        # Access logs for webhook requests
        if not settings.is_development:
            logger.add(
                "logs/access.log",
                format=log_format,
                level="INFO",
                rotation="200 MB",
                retention="30 days",
                compression="zip",
                enqueue=True,
                filter=lambda record: "access" in record["extra"]
            )

        logger.info(f"Logging initialized - Environment: {settings.environment}, Level: {settings.log_level}")

    def _json_formatter(self, record):
        """JSON formatter for production logs"""
        log_entry = {
            "timestamp": record["time"].isoformat(),
            "level": record["level"].name,
            "logger": record["name"],
            "function": record["function"],
            "line": record["line"],
            "message": record["message"],
            "environment": settings.environment
        }

        # Add extra fields if present
        if record["extra"]:
            log_entry.update(record["extra"])

        # Add exception info if present
        if record["exception"]:
            log_entry["exception"] = {
                "type": record["exception"].type.__name__,
                "value": str(record["exception"].value),
                "traceback": record["exception"].traceback
            }

        return json.dumps(log_entry, ensure_ascii=False)

    @staticmethod
    def log_user_interaction(user_id: int, message: str, response: str,
                           rudeness_level: int, processing_time: float):
        """Log user interactions for analytics"""
        logger.bind(
            event_type="user_interaction",
            user_id=user_id,
            message_length=len(message),
            response_length=len(response),
            rudeness_level=rudeness_level,
            processing_time_ms=round(processing_time * 1000, 2)
        ).info("User interaction processed")

    @staticmethod
    def log_rate_limit(user_id: int, endpoint: str):
        """Log rate limiting events"""
        logger.bind(
            event_type="rate_limit",
            user_id=user_id,
            endpoint=endpoint
        ).warning("Rate limit triggered")

    @staticmethod
    def log_webhook_request(update_id: int, user_id: int, message_type: str,
                          processing_time: float, status: str):
        """Log webhook requests"""
        logger.bind(
            access=True,
            event_type="webhook_request",
            update_id=update_id,
            user_id=user_id,
            message_type=message_type,
            processing_time_ms=round(processing_time * 1000, 2),
            status=status
        ).info("Webhook request processed")

    @staticmethod
    def log_ai_service_call(user_id: int, rudeness_level: int, excuse_count: int,
                          response_time: float, token_count: int = None):
        """Log AI service calls for monitoring"""
        logger.bind(
            event_type="ai_service_call",
            user_id=user_id,
            rudeness_level=rudeness_level,
            excuse_count=excuse_count,
            response_time_ms=round(response_time * 1000, 2),
            token_count=token_count
        ).info("AI service call completed")

    @staticmethod
    def log_error(error: Exception, context: Dict[str, Any] = None):
        """Enhanced error logging with context"""
        error_context = {
            "event_type": "error",
            "error_type": type(error).__name__,
            "error_message": str(error)
        }

        if context:
            error_context.update(context)

        logger.bind(**error_context).error(f"Error occurred: {error}")


# Global logger instance
structured_logger = StructuredLogger()


def setup_logging():
    """Setup logging - for backward compatibility"""
    global structured_logger
    if not structured_logger:
        structured_logger = StructuredLogger()


def get_logger():
    """Get the structured logger instance"""
    return structured_logger