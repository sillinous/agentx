"""
Structured Logging Configuration - Production-ready logging with JSON support.

Provides configurable logging that supports:
- Human-readable format for development
- JSON format for production (log aggregation tools like ELK, Datadog)
- Request ID tracing for distributed debugging
- Configurable log levels per module
"""

import logging
import json
import os
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from contextvars import ContextVar

# Context variable for request-scoped data
request_id_var: ContextVar[str] = ContextVar('request_id', default='')


class JSONFormatter(logging.Formatter):
    """
    JSON log formatter for structured logging.

    Outputs logs in JSON format for easy parsing by log aggregation tools.
    """

    def __init__(self, service_name: str = "devops-hub"):
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": self.service_name,
        }

        # Add request ID if available
        request_id = request_id_var.get()
        if request_id:
            log_data["request_id"] = request_id

        # Add source location
        log_data["source"] = {
            "file": record.filename,
            "line": record.lineno,
            "function": record.funcName,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info),
            }

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in (
                'name', 'msg', 'args', 'created', 'filename', 'funcName',
                'levelname', 'levelno', 'lineno', 'module', 'msecs',
                'pathname', 'process', 'processName', 'relativeCreated',
                'stack_info', 'exc_info', 'exc_text', 'thread', 'threadName',
                'message', 'asctime', 'taskName'
            ):
                log_data[key] = value

        return json.dumps(log_data, default=str)


class ColoredFormatter(logging.Formatter):
    """
    Colored log formatter for human-readable development logs.
    """

    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'

    def format(self, record: logging.LogRecord) -> str:
        # Add color
        color = self.COLORS.get(record.levelname, '')

        # Add request ID if available
        request_id = request_id_var.get()
        request_id_str = f"[{request_id[:8]}] " if request_id else ""

        # Format timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Build message
        message = record.getMessage()

        formatted = (
            f"{color}{timestamp} {record.levelname:8}{self.RESET} "
            f"{request_id_str}"
            f"[{record.name}] {message}"
        )

        if record.exc_info:
            formatted += "\n" + self.formatException(record.exc_info)

        return formatted


def configure_logging(
    log_level: Optional[str] = None,
    json_format: Optional[bool] = None,
    service_name: str = "devops-hub",
) -> None:
    """
    Configure application logging.

    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: If True, use JSON format; if False, use colored format
        service_name: Service name for JSON logs
    """
    # Get configuration from environment if not provided
    if log_level is None:
        log_level = os.environ.get("LOG_LEVEL", "INFO").upper()

    if json_format is None:
        json_format = os.environ.get("LOG_FORMAT", "").lower() == "json"

    # Validate log level
    numeric_level = getattr(logging, log_level, logging.INFO)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)

    # Set formatter based on configuration
    if json_format:
        formatter = JSONFormatter(service_name=service_name)
    else:
        formatter = ColoredFormatter()

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Configure specific loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(numeric_level)

    # Log configuration
    root_logger.info(
        f"Logging configured: level={log_level}, format={'json' if json_format else 'colored'}"
    )


def get_request_id() -> str:
    """Get the current request ID."""
    return request_id_var.get()


def set_request_id(request_id: Optional[str] = None) -> str:
    """
    Set the request ID for the current context.

    Args:
        request_id: Request ID to set, or None to generate a new one

    Returns:
        The request ID that was set
    """
    if request_id is None:
        request_id = str(uuid.uuid4())
    request_id_var.set(request_id)
    return request_id


def clear_request_id() -> None:
    """Clear the request ID for the current context."""
    request_id_var.set('')


class LoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that automatically includes extra context.
    """

    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        extra = kwargs.get('extra', {})
        extra['request_id'] = get_request_id()
        kwargs['extra'] = extra
        return msg, kwargs


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the given name.

    This is the preferred way to get loggers in the application.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger
    """
    return logging.getLogger(name)
