from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class FeedbackRating(str, Enum):
    LIKE = "like"
    DISLIKE = "dislike"


class FeedbackCategory(str, Enum):
    ACCURACY = "accuracy"
    COMPLETENESS = "completeness"
    RELEVANCE = "relevance"
    USEFULNESS = "usefulness"
    OVERALL = "overall"


class UserFeedback(BaseModel):
    id: Optional[str] = Field(None, description="Unique feedback identifier")
    user_id: str = Field(..., description="ID of the user providing feedback")
    analysis_id: str = Field(..., description="ID of the analysis being rated")
    analysis_type: str = Field(..., description="Type of analysis (competitor/persona)")
    
    # Rating data
    rating: FeedbackRating = Field(..., description="Like or dislike rating")
    category: FeedbackCategory = Field(default=FeedbackCategory.OVERALL, description="Category of feedback")
    
    # Comment data
    comment: Optional[str] = Field(None, max_length=1000, description="User's detailed comment")
    
    # Specific feedback fields
    accuracy_score: Optional[int] = Field(None, ge=1, le=5, description="Accuracy rating (1-5)")
    usefulness_score: Optional[int] = Field(None, ge=1, le=5, description="Usefulness rating (1-5)")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When feedback was created")
    updated_at: Optional[datetime] = Field(None, description="When feedback was last updated")
    
    # Context data
    user_agent: Optional[str] = Field(None, description="User's browser/app info")
    session_id: Optional[str] = Field(None, description="User session identifier")


class FeedbackCreate(BaseModel):
    analysis_id: str = Field(..., description="ID of the analysis to rate")
    rating: FeedbackRating = Field(..., description="Like or dislike rating")
    category: FeedbackCategory = Field(default=FeedbackCategory.OVERALL, description="Category of feedback")
    comment: Optional[str] = Field(None, max_length=1000, description="Optional detailed comment")
    accuracy_score: Optional[int] = Field(None, ge=1, le=5, description="Accuracy rating (1-5)")
    usefulness_score: Optional[int] = Field(None, ge=1, le=5, description="Usefulness rating (1-5)")


class FeedbackUpdate(BaseModel):
    rating: Optional[FeedbackRating] = Field(None, description="Updated like/dislike rating")
    category: Optional[FeedbackCategory] = Field(None, description="Updated category")
    comment: Optional[str] = Field(None, max_length=1000, description="Updated comment")
    accuracy_score: Optional[int] = Field(None, ge=1, le=5, description="Updated accuracy rating")
    usefulness_score: Optional[int] = Field(None, ge=1, le=5, description="Updated usefulness rating")


class FeedbackResponse(BaseModel):
    id: str = Field(..., description="Feedback identifier")
    analysis_id: str = Field(..., description="Analysis identifier")
    rating: FeedbackRating = Field(..., description="Like or dislike rating")
    category: FeedbackCategory = Field(..., description="Feedback category")
    comment: Optional[str] = Field(None, description="User comment")
    accuracy_score: Optional[int] = Field(None, description="Accuracy rating")
    usefulness_score: Optional[int] = Field(None, description="Usefulness rating")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    can_edit: bool = Field(default=True, description="Whether user can edit this feedback")


class AnalysisFeedbackSummary(BaseModel):
    analysis_id: str = Field(..., description="Analysis identifier")
    analysis_type: str = Field(..., description="Type of analysis")
    
    # Overall metrics
    total_feedback: int = Field(default=0, description="Total number of feedback items")
    likes: int = Field(default=0, description="Number of likes")
    dislikes: int = Field(default=0, description="Number of dislikes")
    like_percentage: float = Field(default=0.0, description="Percentage of likes")
    
    # Score averages
    avg_accuracy: Optional[float] = Field(None, description="Average accuracy score")
    avg_usefulness: Optional[float] = Field(None, description="Average usefulness score")
    
    # Category breakdown
    category_breakdown: Dict[str, int] = Field(default_factory=dict, description="Feedback count by category")
    
    # Comments
    has_comments: bool = Field(default=False, description="Whether there are comments")
    total_comments: int = Field(default=0, description="Number of comments")
    
    # User's feedback (if authenticated)
    user_feedback: Optional[FeedbackResponse] = Field(None, description="Current user's feedback")


class ModelPerformanceMetrics(BaseModel):
    analysis_type: str = Field(..., description="Type of analysis (competitor/persona)")
    time_period: str = Field(..., description="Time period for metrics")
    
    # Overall performance
    total_analyses: int = Field(default=0, description="Total analyses in period")
    total_feedback: int = Field(default=0, description="Total feedback received")
    feedback_rate: float = Field(default=0.0, description="Percentage of analyses with feedback")
    
    # Rating metrics
    overall_like_rate: float = Field(default=0.0, description="Overall like percentage")
    avg_accuracy_score: Optional[float] = Field(None, description="Average accuracy score")
    avg_usefulness_score: Optional[float] = Field(None, description="Average usefulness score")
    
    # Category performance
    accuracy_like_rate: float = Field(default=0.0, description="Like rate for accuracy category")
    completeness_like_rate: float = Field(default=0.0, description="Like rate for completeness category")
    relevance_like_rate: float = Field(default=0.0, description="Like rate for relevance category")
    usefulness_like_rate: float = Field(default=0.0, description="Like rate for usefulness category")
    
    # Trends
    improvement_trend: Optional[str] = Field(None, description="Whether performance is improving/declining")
    most_liked_features: List[str] = Field(default_factory=list, description="Most appreciated features")
    improvement_areas: List[str] = Field(default_factory=list, description="Areas needing improvement")


class FeedbackAnalytics(BaseModel):
    total_feedback: int = Field(default=0, description="Total feedback across all analyses")
    overall_satisfaction: float = Field(default=0.0, description="Overall satisfaction percentage")
    
    # By analysis type
    competitor_metrics: ModelPerformanceMetrics
    persona_metrics: ModelPerformanceMetrics
    
    # Top insights
    most_liked_analyses: List[str] = Field(default_factory=list, description="IDs of most liked analyses")
    most_commented_analyses: List[str] = Field(default_factory=list, description="IDs of most commented analyses")
    
    # Recent trends
    recent_feedback_trend: str = Field(default="stable", description="Recent feedback trend")
    key_insights: List[str] = Field(default_factory=list, description="Key insights from feedback")


class FeedbackBulkResponse(BaseModel):
    feedback_list: List[FeedbackResponse] = Field(default_factory=list, description="List of feedback items")
    total_count: int = Field(default=0, description="Total feedback count")
    has_more: bool = Field(default=False, description="Whether there are more items")
    next_cursor: Optional[str] = Field(None, description="Cursor for pagination") 