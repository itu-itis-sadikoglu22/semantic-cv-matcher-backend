from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.db_test import router as db_test_router
from app.api.routes.health import router as health_router
from app.core.config import settings
from app.api.routes.cv import router as cv_router
from app.api.routes.job import router as job_router
from app.api.routes.ner import router as ner_router
from app.api.routes.embedding import router as embedding_router
from app.api.routes.match import router as match_router

# Initialize FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-powered semantic CV and job matching backend service.",
    version=settings.API_VERSION
)

# Enable CORS for React frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # We allow all origins during development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(health_router, prefix="/api")
app.include_router(db_test_router, prefix="/api")
app.include_router(cv_router, prefix="/api", tags=["CV Ingestion"])
app.include_router(job_router, prefix="/api", tags=["Job Ingestion"])
app.include_router(ner_router, prefix="/api", tags=["NER Extraction"])
app.include_router(embedding_router, prefix="/api", tags=["Embedding"])
app.include_router(match_router, prefix="/api", tags=["Matching"])

@app.get("/")
async def root():
    """
    Root health check endpoint.
    """
    return {
        "status": "running",
        "message": f"{settings.PROJECT_NAME} is active",
        "environment": settings.ENVIRONMENT
    }