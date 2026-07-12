from fastapi import APIRouter, Depends

from app.lifecycle import get_service_container
from app.models import DeanonymizeRequest, DeanonymizeResponse
from app.services.container import ServiceContainer
from app.services.main_service import Santilizer

from .utils import sha_256, to_http_error


router = APIRouter()


@router.post("/deanonymize")
async def deanonymize(
    request: DeanonymizeRequest,
    service_container: ServiceContainer = Depends(get_service_container),
) -> DeanonymizeResponse:
    try:
        text = Santilizer.deanonymize(
            text=request.text,
            engine_result=request.engine_result.to_presidio(),
            service_container=service_container,
        )
        return DeanonymizeResponse(
            sha_256=sha_256(request.text),
            text=text,
        )
    except Exception as error:
        raise to_http_error(error) from error
