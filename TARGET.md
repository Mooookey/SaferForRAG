# 依赖
请你先查看AGENTS.md重点查看链接中的文档。
# 背景
我目前需要利用PaddleNLP对本系统能识别的实体进行扩充，补全presidio传统NER模型不足的短板。
我打算使用信息抽取information_extraction，并使用uie-medical-base作为医疗实体识别，使用uie-m-base作为通用实体识别。具体例子已经在example/paddle中给出。我目前对识别规则做了以下更改：
1.建立了统一实体规则ENTITY_CATALOG: dict[str, EntityDefinition]，之后脱敏用该字典的键作为唯一实体识别符

2.这里需要分别提取中文实体抽取、英文实体抽取和医疗实体抽取，分别给uie-m-base、uie-m-base、uie-medical-base，从而得到paddle_calls


# 要求

@app.post("/extract")
async def extract(text: str, schema: dict):
    taskflow = await factory.get_pipeline(schema)
    try:
        return taskflow(text)
    finally:
        await factory.return_pipeline(taskflow)  # 无论如何都要归还


请你给出logger/config.py的代码实现，但不写进代码，要求分为多个主要函数或者由一个类分别管理，或者你有更规范的编写方式的话更好，分别为：
1. 对内部库的日志进行重定向，拦截并输出到service.log中：
    - 采用点名拦截+清掉handler+阻止传递到root，级别设置为INFO
    - 除了拦截并重定向presidio/paddlenlp，要求能拦截llm guard配置的structlog日志
2. 外部请求响应记录到app.log
    - 设置.propagate = False
    - 同时给出@app.middleware("http")的中间件的代码实现，记录method / path / status_code / 耗时 / 响应的sha_256
3. 当设置环境变量DEBUG_LOG_ENABLED==True时，开启调试日志，将请求体和响应体完整记录到logs/debug.log
    - 采用RotatingFileHandler
    - 在2.中的中间件增加开关，并且写到该中间件中
4. 所有日志，需要同时输出到控制台，并且共享一个实例
5. 需要幂等，开头对目标 logger 先 handlers.clear()




```python

from __future__ import annotations

import json
import logging
import os
import sys
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler
from pathlib import Path
from time import perf_counter
from typing import AsyncIterator

import structlog
from fastapi import FastAPI, Request


LOG_DIR = Path("logs")

APP_LOGGER_NAME = "app.http"
DEBUG_LOGGER_NAME = "app.http.debug"

# 根据项目当前依赖版本中的实际 logger 名称点名拦截。
SERVICE_LOGGER_NAMES = (
    "presidio-analyzer",
    "presidio-anonymizer",
    "decision_process",
    "PaddleNLP",
    "paddlenlp",
    "llm_guard",
)

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


@dataclass(frozen=True, slots=True)
class Loggers:
    app: logging.Logger
    debug: logging.Logger | None

# 此处是全局实例
_shared_loggers: Loggers | None = None


def _debug_log_enabled() -> bool:
    """仅当环境变量严格等于 True 时启用调试日志。"""
    return os.getenv("DEBUG_LOG_ENABLED") == "True"


def _create_file_handler(filename: str) -> RotatingFileHandler:
    MAX_LOG_BYTES = 20 * 1024 * 1024
    BACKUP_COUNT = 3
    handler = RotatingFileHandler(
        filename=LOG_DIR / filename,
        maxBytes=MAX_LOG_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    return handler


def _create_console_handler() -> logging.StreamHandler:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    return handler


def _replace_handlers(
    logger: logging.Logger,
    handlers: tuple[logging.Handler, ...],
    level: int,
) -> None:
    """
    幂等配置目标 logger。

    每个目标 logger 均先清空 handlers，防止重复调用配置时产生重复输出。
    """
    logger.handlers.clear()
    logger.setLevel(level)
    logger.propagate = False

    for handler in handlers:
        logger.addHandler(handler)


def _configure_structlog() -> None:
    """
    将 llm-guard 的 structlog 输出接入标准库 logging。

    llm-guard 0.3.16 默认使用 PrintLoggerFactory，直接向 stream 写入，
    无法由 logging handler 截获。这里改为 LoggerFactory，使名为
    llm_guard 的 structlog logger 进入 logging.getLogger("llm_guard")。
    """
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


def _configure_service_loggers(
    service_file_handler: logging.Handler,
    console_handler: logging.Handler,
) -> None:
    _configure_structlog()

    # 所有内部库共享 service.log handler 和同一个控制台 handler。
    shared_handlers = (
        service_file_handler,
        console_handler,
    )

    for logger_name in SERVICE_LOGGER_NAMES:
        service_logger = logging.getLogger(logger_name)

        _replace_handlers(
            logger=service_logger,
            handlers=shared_handlers,
            level=logging.INFO,
        )


def _configure_app_logger(
    app_file_handler: logging.Handler,
    console_handler: logging.Handler,
) -> logging.Logger:
    app_logger = logging.getLogger(APP_LOGGER_NAME)

    _replace_handlers(
        logger=app_logger,
        handlers=(
            app_file_handler,
            console_handler,
        ),
        level=logging.INFO,
    )

    return app_logger


def _configure_debug_logger(
    debug_file_handler: logging.Handler,
    console_handler: logging.Handler,
) -> logging.Logger:
    debug_logger = logging.getLogger(DEBUG_LOGGER_NAME)
    debug_logger.disabled = False

    _replace_handlers(
        logger=debug_logger,
        handlers=(
            debug_file_handler,
            console_handler,
        ),
        level=logging.DEBUG,
    )

    return debug_logger


def _disable_debug_logger() -> None:
    debug_logger = logging.getLogger(DEBUG_LOGGER_NAME)

    debug_logger.handlers.clear()
    debug_logger.propagate = False
    debug_logger.disabled = True


def setup_logging() -> Loggers:
    """
    配置日志系统并返回整个应用共享的 logger 集合。

    首次调用完成配置，后续调用直接返回同一实例。
    """
    global _shared_loggers

    if _shared_loggers is not None:
        return _shared_loggers

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # 所有日志共享同一个控制台 handler 实例。
    console_handler = _create_console_handler()

    app_file_handler = _create_file_handler("app.log")
    service_file_handler = _create_file_handler("service.log")

    _configure_service_loggers(
        service_file_handler=service_file_handler,
        console_handler=console_handler,
    )

    app_logger = _configure_app_logger(
        app_file_handler=app_file_handler,
        console_handler=console_handler,
    )

    debug_logger: logging.Logger | None = None

    if _debug_log_enabled():
        debug_file_handler = _create_file_handler("debug.log")

        debug_logger = _configure_debug_logger(
            debug_file_handler=debug_file_handler,
            console_handler=console_handler,
        )
    else:
        _disable_debug_logger()

    _shared_loggers = Loggers(
        app=app_logger,
        debug=debug_logger,
    )

    return _shared_loggers


def _extract_sha_256(response_body: bytes) -> str | None:
    """
    提取 Controller 响应模型顶层的 sha_256 字段。

    健康检查和错误响应中没有该字段，此时返回 None。
    """
    response_data = json.loads(response_body)
    return response_data.get("sha_256")


def install_http_logging_middleware(app: FastAPI) -> None:
    loggers = setup_logging()

    @app.middleware("http")
    async def http_logging_middleware(request: Request, call_next):
        started_at = perf_counter()

        request_body: bytes | None = None

        if loggers.debug is not None:
            request_body = await request.body()

        response = await call_next(request)

        # 读取完整响应体，以提取 Controller 返回的 sha_256，
        # 同时为 debug.log 记录完整响应内容。
        response_chunks = [
            bytes(chunk)
            async for chunk in response.body_iterator
        ]
        response_body = b"".join(response_chunks)

        # body_iterator 被读取后必须恢复，否则客户端会收到空响应体。
        async def replay_response_body() -> AsyncIterator[bytes]:
            yield response_body

        response.body_iterator = replay_response_body()

        elapsed_ms = (perf_counter() - started_at) * 1000

        response_sha_256 = _extract_sha_256(response_body)

        # /health 和错误响应没有 sha_256，日志中使用 "-" 表示。
        loggers.app.info(
            "method=%s | path=%s | status_code=%d | "
            "elapsed_ms=%.3f | sha_256=%s",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
            response_sha_256 or "-",
        )

        if loggers.debug is not None:
            loggers.debug.debug(
                "method=%s | path=%s | request_body=%r | response_body=%r",
                request.method,
                request.url.path,
                request_body,
                response_body,
            )

        return response



```