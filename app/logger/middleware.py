import json
from time import perf_counter
from typing import AsyncIterator, cast

from fastapi import FastAPI, Request
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response, StreamingResponse

from app.logger.manager import LoggingManager
from app.logger.models import LoggerSet


class ResponseExtractor:
    def extract_sha256(self, body: bytes) -> str | None:
        data: dict[str, object] = json.loads(body)
        return cast(str | None, data.get("sha_256"))


class HTTPLoggingMiddlewareInstaller:
    def __init__(
        self,
        logging_manager: LoggingManager,
        extractor: ResponseExtractor,
    ) -> None:
        self.logging_manager: LoggingManager = logging_manager
        self.extractor: ResponseExtractor = extractor

    def install(self, app: FastAPI) -> None:
        loggers: LoggerSet = self.logging_manager.initialize()

        @app.middleware("http")
        async def middleware(
            request: Request,
            call_next: RequestResponseEndpoint,
        ) -> Response:
            start: float = perf_counter()

            request_body: bytes | None = None
            if loggers.debug is not None:
                request_body = await request.body()

            response: StreamingResponse = cast(
                StreamingResponse,
                await call_next(request),
            )

            chunks: list[bytes] = []
            chunk: bytes | memoryview
            async for chunk in response.body_iterator:
                chunks.append(bytes(chunk))
            body: bytes = b"".join(chunks)

            async def replay() -> AsyncIterator[bytes]:
                yield body

            response.body_iterator = replay()

            elapsed: float = (perf_counter() - start) * 1000

            sha256: str | None = self.extractor.extract_sha256(body)

            loggers.app.info(
                "method=%s | path=%s | status_code=%d | "
                "elapsed_ms=%.3f | sha_256=%s",
                request.method,
                request.url.path,
                response.status_code,
                elapsed,
                sha256 or "-",
            )

            if loggers.debug is not None:
                loggers.debug.debug(
                    "method=%s | path=%s | request_body=%r | response_body=%r",
                    request.method,
                    request.url.path,
                    request_body,
                    body,
                )

            return response
