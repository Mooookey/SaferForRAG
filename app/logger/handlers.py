import logging
import sys
from logging.handlers import RotatingFileHandler

from app.logger.models import LoggingConfig


class LogHandlerFactory:
    @staticmethod
    def create_file(filename: str) -> RotatingFileHandler:
        handler: RotatingFileHandler = RotatingFileHandler(
            filename=LoggingConfig.LOG_DIR / filename,
            maxBytes=LoggingConfig.MAX_BYTES,
            backupCount=LoggingConfig.BACKUP_COUNT,
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter(LoggingConfig.FORMAT))
        return handler

    @staticmethod
    def create_console() -> logging.StreamHandler:
        handler: logging.StreamHandler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(LoggingConfig.FORMAT))
        return handler
