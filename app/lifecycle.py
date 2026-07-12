from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from app.services.container import ServiceContainer


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.service_container = ServiceContainer()
    yield


async def get_service_container(request: Request) -> ServiceContainer:
    return request.app.state.service_container
