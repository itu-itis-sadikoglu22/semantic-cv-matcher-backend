from pydantic import BaseModel


class MessageResponse(BaseModel):
    """
    Generic message response schema for delete and status operations.
    """

    message: str