from fastapi import APIRouter, Depends

from app.lifecycle import get_service_container
from app.models import RecognizerResultModel, ScanRequest, ScanResponse
from app.services.container import ServiceContainer
from app.services.Sanitizer import Sanitizer

from .utils import sha_256, to_http_error


router = APIRouter()


@router.post("/scan")
async def scan(
    request: ScanRequest,
    service_container: ServiceContainer = Depends(get_service_container),
) -> ScanResponse:
    try:
        results = Sanitizer.scan(
            text=request.text,
            service_container=service_container,
            profile=request.profile,
            policy=request.policy,
        )
        return ScanResponse(
            sha_256=sha_256(request.text),
            results=[RecognizerResultModel.from_presidio(result) for result in results],
        )
    except Exception as error:
        raise to_http_error(error) from error
