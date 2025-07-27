from pydantic import BaseModel, Field
from typing import Optional
from core.persona_models import PersonaReport


class PersonaAnalysisRequest(BaseModel):
    """
    Request schema for persona analysis
    """
    business_idea: str = Field(
        ..., 
        description="Description of the business idea or product",
        example="AI-powered fitness app that creates personalized workout plans"
    )
    target_market: Optional[str] = Field(
        None,
        description="Target market or customer segment", 
        example="Fitness enthusiasts aged 25-45 who work out at home"
    )
    industry: Optional[str] = Field(
        None,
        description="Industry vertical",
        example="Health and Fitness Technology"
    )
    geographic_focus: Optional[str] = Field(
        None,
        description="Target geographic markets",
        example="North America and Europe"
    )
    product_category: Optional[str] = Field(
        None,
        description="Product category or type",
        example="Mobile App"
    )
    idea_id: Optional[str] = Field(
        None,
        description="Business idea ID (for authenticated users to save results)",
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