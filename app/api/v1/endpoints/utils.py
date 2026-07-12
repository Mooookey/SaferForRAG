import hashlib

from fastapi import HTTPException

from app.services.ServiceError import ServiceError


def sha_256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def to_http_error(error: Exception) -> HTTPException:
    if isinstance(error, ServiceError):
        return HTTPException(
            status_code=400,
            detail={"code": error.code, "message": error.message},
        )
    return HTTPException(
        status_code=400,
        detail={"code": "BAD_REQUEST", "message": str(error)},
    )
