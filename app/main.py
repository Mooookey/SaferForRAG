from fastapi import FastAPI

from app.api.v1.router import router as api_v1_router
from app.lifecycle import lifespan


app = FastAPI(lifespan=lifespan)
app.include_router(api_v1_router, prefix="/api/v1")
