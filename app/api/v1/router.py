from fastapi import APIRouter

from app.api.v1.endpoints import (
    anonymize,
    check_input,
    check_output,
    deanonymize,
    health,
    scan,
)


router = APIRouter()
router.include_router(health.router)
router.include_router(scan.router)
router.include_router(anonymize.router)
router.include_router(deanonymize.router)
router.include_router(check_input.router)
router.include_router(check_output.router)
