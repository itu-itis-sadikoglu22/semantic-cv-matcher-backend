from pydantic import BaseModel


class HealthResponse(BaseModel):
    """
    Response schema for health check endpoint.
    """

    status: str
    service: str