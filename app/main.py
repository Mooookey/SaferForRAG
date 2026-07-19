from fastapi import FastAPI

from app.api.v1.router import router as api_v1_router
from app.lifecycle import lifespan
from app.logger.manager import LoggingManager
from app.logger.middleware import (
    HTTPLoggingMiddlewareInstaller,
    ResponseExtractor,
)


logging_manager: LoggingManager = LoggingManager()

middleware_installer: HTTPLoggingMiddlewareInstaller = (
    HTTPLoggingMiddlewareInstaller(
        logging_manager=logging_manager,
        extractor=ResponseExtractor(),
    )
)

app: FastAPI = FastAPI(lifespan=lifespan)

middleware_installer.install(app)

app.include_router(api_v1_router, prefix="/api/v1",)