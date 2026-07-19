import logging
import os

import structlog

from app.logger.handlers import LogHandlerFactory
from app.logger.models import LoggerSet, LoggingConfig


class LoggingManager:
    def __init__(self, handler_factory: LogHandlerFactory | None = None) -> None:
        self.handler_factory: LogHandlerFactory = handler_factory or LogHandlerFactory()
        self._loggers: LoggerSet | None = None

    def initialize(self) -> LoggerSet:
        if self._loggers is not None:
            return self._loggers

        LoggingConfig.LOG_DIR.mkdir(parents=True, exist_ok=True)
        console: logging.StreamHandler = self.handler_factory.create_console()
        app_handler: logging.Handler = self.handler_factory.create_file(
            LoggingConfig.APP_FILE
        )
        service_handler: logging.Handler = self.handler_factory.create_file(
            LoggingConfig.SERVICE_FILE
        )

        self._configure_structlog()
        self._configure_service(service_handler, console)

        app_logger: logging.Logger = self._configure_logger(
            LoggingConfig.APP_LOGGER,
            (app_handler, console),
            logging.INFO,
        )

        debug_logger: logging.Logger | None = None
        if self.debug_enabled():
            debug_handler: logging.Handler = self.handler_factory.create_file(
                LoggingConfig.DEBUG_FILE
            )
            debug_logger = self._configure_logger(
                LoggingConfig.DEBUG_LOGGER,
                (debug_handler, console),
                logging.DEBUG,
            )
        else:
            self.disable(LoggingConfig.DEBUG_LOGGER)

        self._loggers = LoggerSet(app=app_logger, debug=debug_logger)
        return self._loggers

    def _configure_logger(
        self,
        name: str,
        handlers: tuple[logging.Handler, ...],
        level: int,
    ) -> logging.Logger:
        logger: logging.Logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.disabled = False
        logger.setLevel(level)
        logger.propagate = False
        handler: logging.Handler
        for handler in handlers:
            logger.addHandler(handler)
        return logger

    def _configure_service(
        self,
        file_handler: logging.Handler,
        console: logging.Handler,
    ) -> None:
        handlers: tuple[logging.Handler, ...] = (file_handler, console)
        name: str
        for name in LoggingConfig.SERVICE_LOGGERS:
            self._configure_logger(name, handlers, logging.INFO)

    def disable(self, name: str) -> None:
        logger: logging.Logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.propagate = False
        logger.disabled = True

    def debug_enabled(self) -> bool:
        return os.getenv("DEBUG_LOG_ENABLED") == "True"

    def _configure_structlog(self) -> None:
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.JSONRenderer(ensure_ascii=False),
            ],
            context_class=dict,
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=False,
        )
