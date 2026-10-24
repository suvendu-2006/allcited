from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Verify settings load cleanly on startup
    settings = get_settings()
    app.state.settings = settings
    yield


settings = get_settings()

app = FastAPI(
    title="Allcited API",
    version="0.1.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/v1/health")
async def health():
    return {
        "status": "ok",
        "version": "0.1.0",
        "mode": settings.MODE,
        "environment": settings.ENVIRONMENT,
    }
