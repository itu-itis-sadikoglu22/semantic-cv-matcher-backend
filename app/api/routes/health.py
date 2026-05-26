from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint for backend status monitoring.
    """
    return {
        "status": "healthy",
        "service": "semantic-cv-matcher-backend"
    }