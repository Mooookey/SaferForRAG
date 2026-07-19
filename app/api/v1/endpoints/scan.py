import json
import logging

from fastapi import APIRouter, Depends

from app.lifecycle import get_service_container
from app.logger.models import LoggingConfig
from app.models import RecognizerResultModel, ScanRequest, ScanResponse
from app.services.container import ServiceContainer
from app.services.Sanitizer import Sanitizer

from .utils import sha_256, to_http_error


router: APIRouter = APIRouter()
app_logger: logging.Logger = logging.getLogger(LoggingConfig.APP_LOGGER)


@router.post("/scan")
async def scan(
    request: ScanRequest,
    service_container: ServiceContainer = Depends(get_service_container),
) -> ScanResponse:
    try:
        results = await Sanitizer.scan(
            text=request.text,
            service_container=service_container,
            profile=request.profile,
            policy=request.policy,
        )

        request_sha_256: str = sha_256(request.text)

        # 捕获scan service的metadata，包括recognizer_name，sources，model，raw_label
        trace_results: list[dict[str, object]] = [
            {
                "entity_type": result.entity_type,
                "start": result.start,
                "end": result.end,
                "score": result.score,
                "metadata": result.recognition_metadata,
            }
            for result in results
        ]

        app_logger.info(
            "scan_trace | sha_256=%s | results=%s",
            request_sha_256,
            json.dumps(trace_results, ensure_ascii=False),
        )

        return ScanResponse(
            sha_256=request_sha_256,
            results=[
                RecognizerResultModel.from_presidio(result)
                for result in results
            ],
        )
    except Exception as error:
        raise to_http_error(error) from error