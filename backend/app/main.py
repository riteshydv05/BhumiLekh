import logging

from fastapi import FastAPI

from app.api.v1.documents import router as documents_router
from app.api.v1.integration import router as integration_router

# Import all models so SQLAlchemy's metadata is aware of them for create_all
import app.models  # noqa: F401

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)

from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi import Request

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database migrations are run automatically on startup
    try:
        from app.db.migrate import run_migrations
        run_migrations()
        logging.info("Startup database migrations completed.")
    except Exception as exc:
        logging.error("Failed to run startup database migrations: %s", exc)
    yield

app = FastAPI(
    title="Land Record AI System",
    description="Intelligent Land Record Digitization and Validation System",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*",
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.exception("Unhandled server exception on %s %s: %s", request.method, request.url.path, exc)
    response = JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "error": str(exc)},
    )
    origin = request.headers.get("origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

# Integration router must be registered BEFORE documents router
# because documents has /{document_id} catch-all patterns
app.include_router(
    integration_router,
    prefix="/api/v1",
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
