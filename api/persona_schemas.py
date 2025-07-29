from pydantic import BaseModel, Field
from typing import Optional
from core.persona_models import PersonaReport


class PersonaAnalysisRequest(BaseModel):
    """
    Request schema for persona analysis
    """
    idea_id: str = Field(
        ...,
        description="Business idea ID to analyze",
        example="550e8400-e29b-41d4-a716-446655440000"
    )


class PersonaAnalysisResponse(BaseModel):
    """
    Response schema for persona analysis
    """
    status: str = Field(
        ...,
        description="Analysis status",
        example="completed"
    )
    report: Optional[PersonaReport] = Field(
        None,
        description="Persona analysis report with detailed personas"
    )
    analysis_id: Optional[str] = Field(
        None,
        description="Analysis ID (included when saved for authenticated users)",
        example="550e8400-e29b-41d4-a716-446655440000"
    )
    message: str = Field(
        ...,
        description="Response message",
        example="Persona analysis completed successfully"
    )


class PersonaStatusResponse(BaseModel):
    """
    Response schema for persona analysis status check
    """
    status: str = Field(
        ...,
        description="Current analysis status",
        example="processing"
    )
    progress: Optional[int] = Field(
        None,
        description="Progress percentage (0-100)",
        example=75
    )
    started_at: Optional[str] = Field(
        None,
        description="Analysis start timestamp",
        example="2024-01-15T10:30:00Z"
    )
    completed_at: Optional[str] = Field(
        None,
        description="Analysis completion timestamp"
    )
    message: str = Field(
        ...,
        description="Status message",
        example="Persona analysis in progress"
    )
    error: Optional[str] = Field(
        None,
        description="Error message if analysis failed"
    )