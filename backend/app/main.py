from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api import auth, audit, datasets, evaluations, llm, models
from app.core.config import settings
from app.core.database import SessionLocal, init_db
from app.services.seed_data import seed_benchmarks_if_empty

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Enforce production security invariants at startup
    settings.validate_runtime()
    # Initialize SQLite database schema
    init_db()
    # Populate benchmark presets for immediate evaluation arena demonstration
    db = SessionLocal()
    try:
        seed_benchmarks_if_empty(db)
    finally:
        db.close()
    yield

app = FastAPI(
    title="Model Evaluation Arena",
    description="Compare model predictions with metrics, bootstrap confidence intervals, and cohort slices",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration for development frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(auth.router)
app.include_router(datasets.router)
app.include_router(models.router)
app.include_router(evaluations.router)
app.include_router(llm.router)
app.include_router(audit.router)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "app_env": settings.app_env,
        "demo_mode": settings.demo_mode,
        "version": "1.0.0",
    }

@app.get("/api/version")
def api_version():
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "author": "Alan Vo",
        "domain": "ai-ml",
    }

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {type(exc).__name__}"},
    )
