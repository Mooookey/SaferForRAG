from fastapi import APIRouter, Depends

from app.lifecycle import get_service_container
from app.models import CheckOutputRequest, CheckResponse
from app.services.container import ServiceContainer
from app.services.Guardian import Guardian

from .utils import sha_256, to_http_error


router = APIRouter()


@router.post("/check_output")
async def check_output(
    request: CheckOutputRequest,
    service_container: ServiceContainer = Depends(get_service_container),
) -> CheckResponse:
    try:
        text, valid, score = Guardian.check_output(
            prompt=request.prompt,
            text=request.text,
            service_container=service_container,
            profile=request.profile,
            policy=request.policy,
        )
        return CheckResponse(
            sha_256=sha_256(request.text),
            text=text,
            valid=valid,
            score=score,
        )
    except Exception as error:
        raise to_http_error(error) from error
