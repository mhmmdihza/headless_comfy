import logging
from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from api.handler.endpoints import router
from fastapi.middleware.cors import CORSMiddleware
from api.config import settings
from api.db.postgres import init_db

from api.middleware.jwt import JWTAuthMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(level=logging.INFO)
    await init_db()
    yield

app = FastAPI(title="AI Image Generator",lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Image-Metadata"],
)
app.add_middleware(JWTAuthMiddleware)
app.include_router(router)
