from fastapi import APIRouter

from app.schemas.health import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse
)
async def health_check():
    """
    Health check endpoint for backend status monitoring.
    """

    return HealthResponse(
        status="healthy",
        service="semantic-cv-matcher-backend"
    )