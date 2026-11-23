"""
Integration Intelligence - Logging Utilities.

Provides structured, colored, contextual logging using Loguru with
standard library interception and rotating log file persistence.
"""

import logging
import sys
from typing import Optional
from loguru import logger

from src.config import Settings, settings as global_settings


class InterceptHandler(logging.Handler):
    """Intercept standard library logging messages and redirect them to Loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def configure_logging(custom_settings: Optional[Settings] = None) -> None:
    """
    Configure global logging format, handlers, and persistence.
    
    Args:
        custom_settings: Optional Settings instance. Defaults to global_settings.
    """
    cfg = custom_settings or global_settings

    # Ensure log output directory exists
    cfg.ensure_directories_exist()

    # Remove all existing handlers from loguru
    logger.remove()

    # Format string for terminal output with colors and module context
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    # Format string for file output
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
        "{level: <8} | "
        "{name}:{function}:{line} - "
        "{message}"
    )

    # Add console sink
    logger.add(
        sys.stderr,
        format=console_format,
        level=cfg.log_level.upper(),
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # Add rotating file sink
    logger.add(
        str(cfg.log_file_path),
        format=file_format,
        level=cfg.log_level.upper(),
        rotation="10 MB",
        retention="14 days",
        compression="zip",
        encoding="utf-8",
        enqueue=True,
    )

    # Intercept root standard library logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Silence overly verbose external loggers
    for noisy_logger in ["httpcore", "httpx", "urllib3", "asyncio"]:
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)

    logger.debug("Structured logging initialized successfully.")


# Auto-configure default logger on module import
configure_logging()


def get_logger(name: Optional[str] = None):
    """Retrieve logger instance, optionally bound with component name."""
    if name:
        return logger.bind(name=name)
    return logger


def setup_logging(custom_settings: Optional[Settings] = None) -> None:
    """Setup logging handler (alias for configure_logging)."""
    configure_logging(custom_settings)

