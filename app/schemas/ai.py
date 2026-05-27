from pydantic import BaseModel


class AIModelInfo(BaseModel):
    """
    Describes a single AI/NLP component used in the backend.
    """

    name: str
    type: str
    purpose: str
    status: str


class AIModelsResponse(BaseModel):
    """
    Describes the AI/NLP layer of the system.
    """

    project_ai_summary: str
    models: list[AIModelInfo]
    planned_improvements: list[str]