from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router

# Initialize FastAPI application
app = FastAPI(
    title="Semantic CV Matcher API",
    description="AI-powered semantic CV and job matching backend service.",
    version="1.0.0"
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


@app.get("/")
async def root():
    """
    Root health check endpoint.
    """
    return {
        "status": "running",
        "message": "Semantic CV Matcher Backend is active"
    }