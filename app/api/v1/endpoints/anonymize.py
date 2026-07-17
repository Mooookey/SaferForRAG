from fastapi import APIRouter, Depends

from app.lifecycle import get_service_container
from app.models import AnonymizeRequest, AnonymizeResponse, EngineResultModel
from app.services.container import ServiceContainer
from app.services.Sanitizer import Sanitizer

from .utils import sha_256, to_http_error


router = APIRouter()


@router.post("/anonymize")
async def anonymize(
    request: AnonymizeRequest,
    service_container: ServiceContainer = Depends(get_service_container),
) -> AnonymizeResponse:
    try:
        analyzer_results = None
        if request.analyzer_results is not None:
            analyzer_results = [result.to_presidio() for result in request.analyzer_results]

        engine_result = Sanitizer.anonymize(
            text=request.text,
            service_container=service_container,
            transformation_profile=request.transformation_profile,
            transformation_policy=request.transformation_policy,
            detection_policy=request.detection_policy,
            analyzer_results=analyzer_results,
        )
        return AnonymizeResponse(
            sha_256=sha_256(request.text),
            engine_result=EngineResultModel.from_presidio(engine_result),
        )
    except Exception as error:
        raise to_http_error(error) from error
