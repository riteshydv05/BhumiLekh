import logging

from fastapi import FastAPI

from app.api.v1.documents import router as documents_router

# Import all models so SQLAlchemy's metadata is aware of them for create_all
import app.models  # noqa: F401

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)

app = FastAPI(
    title="Land Record AI System",
    description="Intelligent Land Record Digitization and Validation System",
    version="1.0.0",
)

app.include_router(
    documents_router,
    prefix="/api/v1",
)


@app.get("/")
def root():
    return {
        "message": "Land Record AI System API",
        "status": "running",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }
