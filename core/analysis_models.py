from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

from core.competitor_models import CompetitorReport
from core.persona_models import PersonaReport
from core.market_models import MarketSizingReport
from core.business_model_models import BusinessModelReport
from core.business_model_canvas_models import BusinessModelCanvas


class AnalysisType(str, Enum):
    COMPETITOR = "competitor"
    PERSONA = "persona"
    MARKET_SIZING = "market_sizing"
    BUSINESS_MODEL = "business_model"
    BUSINESS_MODEL_CANVAS = "business_model_canvas"


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SavedAnalysis(BaseModel):
    id: Optional[str] = Field(None, description="Unique identifier for the analysis")
    user_id: str = Field(..., description="ID of the user who created this analysis")
    idea_id: str = Field(..., description="ID of the business idea this analysis relates to")
    analysis_type: AnalysisType = Field(..., description="Type of analysis (competitor or persona)")
    status: AnalysisStatus = Field(default=AnalysisStatus.PENDING, description="Current status of the analysis")
    
    # Analysis data
    competitor_report: Optional[CompetitorReport] = Field(None, description="Competitor analysis results")
    persona_report: Optional[PersonaReport] = Field(None, description="Persona analysis results")
    market_sizing_report: Optional[MarketSizingReport] = Field(None, description="Market sizing analysis results")
    business_model_report: Optional[BusinessModelReport] = Field(None, description="Business model analysis results")
    business_model_canvas_report: Optional[BusinessModelCanvas] = Field(None, description="Business model canvas results")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the analysis was created")
    completed_at: Optional[datetime] = Field(None, description="When the analysis was completed")
    execution_time: Optional[float] = Field(None, description="Time taken to complete the analysis")
    
    # Error handling
    error_message: Optional[str] = Field(None, description="Error message if analysis failed")
    retry_count: int = Field(default=0, description="Number of times this analysis was retried")
    
    # Feedback metrics (computed fields)
    feedback_summary: Optional[Dict[str, Any]] = Field(None, description="Summary of user feedback")
    has_feedback: bool = Field(default=False, description="Whether this analysis has received feedback")
    like_count: int = Field(default=0, description="Number of likes")
    dislike_count: int = Field(default=0, description="Number of dislikes")
    comment_count: int = Field(default=0, description="Number of comments")
    avg_accuracy_score: Optional[float] = Field(None, description="Average accuracy rating")
    avg_usefulness_score: Optional[float] = Field(None, description="Average usefulness rating")


class AnalysisRequest(BaseModel):
    idea_id: str = Field(..., description="ID of the business idea to analyze")
    analysis_type: AnalysisType = Field(..., description="Type of analysis to perform")
    
    # Optional overrides for the analysis
    custom_description: Optional[str] = Field(None, description="Custom business description override")
    custom_target_market: Optional[str] = Field(None, description="Custom target market override")
    custom_industry: Optional[str] = Field(None, description="Custom industry override")


class AnalysisResponse(BaseModel):
    analysis_id: str = Field(..., description="Unique identifier for the analysis")
    status: AnalysisStatus = Field(..., description="Current status of the analysis")
    message: str = Field(..., description="Status message")
    
    # Results (only included when completed)
    competitor_report: Optional[CompetitorReport] = Field(None, description="Competitor analysis results")
    persona_report: Optional[PersonaReport] = Field(None, description="Persona analysis results")
    
    # Metadata
    created_at: datetime = Field(..., description="When the analysis was created")
    completed_at: Optional[datetime] = Field(None, description="When the analysis was completed")
    execution_time: Optional[float] = Field(None, description="Time taken to complete the analysis")
    
    # Feedback data (only for authenticated users)
    can_provide_feedback: bool = Field(default=False, description="Whether the user can provide feedback")
    feedback_summary: Optional[Dict[str, Any]] = Field(None, description="Summary of feedback for this analysis")
    user_feedback: Optional[Dict[str, Any]] = Field(None, description="Current user's feedback if any")


class AnalysisHistory(BaseModel):
    user_id: str = Field(..., description="User ID")
    idea_id: str = Field(..., description="Business idea ID")
    analyses: List[SavedAnalysis] = Field(default_factory=list, description="List of analyses for this idea")
    total_analyses: int = Field(default=0, description="Total number of analyses")
    last_analysis_date: Optional[datetime] = Field(None, description="Date of the most recent analysis")


class UserAnalyticsSummary(BaseModel):
    user_id: str = Field(..., description="User ID")
    total_ideas: int = Field(default=0, description="Total number of business ideas")
    total_analyses: int = Field(default=0, description="Total number of analyses performed")
    competitor_analyses_count: int = Field(default=0, description="Number of competitor analyses")
    persona_analyses_count: int = Field(default=0, description="Number of persona analyses")
    avg_execution_time: Optional[float] = Field(None, description="Average analysis execution time")
    most_active_idea: Optional[str] = Field(None, description="ID of the most analyzed idea")
    join_date: datetime = Field(..., description="When the user joined")
    last_activity: Optional[datetime] = Field(None, description="Date of last analysis") 