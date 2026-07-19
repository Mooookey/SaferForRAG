from dataclasses import dataclass
from logging import Logger
from pathlib import Path
from typing import ClassVar


@dataclass(frozen=True, slots=True)
class LoggerSet:
    app: Logger
    debug: Logger | None


class LoggingConfig:
    LOG_DIR: ClassVar[Path] = Path("logs")

    APP_LOGGER: ClassVar[str] = "app.http"
    DEBUG_LOGGER: ClassVar[str] = "app.http.debug"

    SERVICE_LOGGERS: ClassVar[tuple[str, ...]] = (
        "presidio-analyzer",
        "presidio-anonymizer",
        "decision_process",
        "PaddleNLP",
        "paddlenlp",
        "llm_guard",
    )

    APP_FILE: ClassVar[str] = "app.log"
    SERVICE_FILE: ClassVar[str] = "service.log"
    DEBUG_FILE: ClassVar[str] = "debug.log"

    MAX_BYTES: ClassVar[int] = 20 * 1024 * 1024
    BACKUP_COUNT: ClassVar[int] = 3

    FORMAT: ClassVar[str] = (
        "%(asctime)s | "
        "%(levelname)s | "
        "%(name)s | "
        "%(message)s"
    )
