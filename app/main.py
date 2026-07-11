from fastapi import FastAPI
from lifecycle import lifespan

app = FastAPI(lifespan=lifespan)