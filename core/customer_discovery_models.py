from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


# Enums
class InterviewType(str, Enum):
    PROBLEM_VALIDATION = "problem_validation"
    SOLUTION_VALIDATION = "solution_validation"
    CUSTOMER_DEVELOPMENT = "customer_development"
    USER_TESTING = "user_testing"
    MARKET_RESEARCH = "market_research"


class InterviewStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    TRANSCRIBED = "transcribed"
    ANALYZED = "analyzed"
    FOLLOW_UP_NEEDED = "follow_up_needed"


class FileType(str, Enum):
    AUDIO = "audio"
    VIDEO = "video"
    TRANSCRIPT = "transcript"


class InsightType(str, Enum):
    PAIN_POINT = "pain_point"
    VALIDATION_POINT = "validation_point"
    FEATURE_REQUEST = "feature_request"
    PRICING_FEEDBACK = "pricing_feedback"
    COMPETITIVE_MENTION = "competitive_mention"
    MARKET_SIZE_INDICATOR = "market_size_indicator"
    PERSONA_CHARACTERISTIC = "persona_characteristic"
    BMC_UPDATE = "bmc_update"


class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class CustomerSegment(str, Enum):
    BUSY_PARENTS = "busy_parents"
    REMOTE_WORKERS = "remote_workers"
    STUDENTS = "students"
    SENIORS = "seniors"
    ENTREPRENEURS = "entrepreneurs"
    OTHER = "other"


class ScoreCategory(str, Enum):
    PROBLEM_CONFIRMATION = "problem_confirmation"
    SOLUTION_INTEREST = "solution_interest"
    WILLINGNESS_TO_PAY = "willingness_to_pay"
    URGENCY = "urgency"
    FREQUENCY = "frequency"
    INTENSITY = "intensity"
    MARKET_SIZE = "market_size"
    COMPETITIVE_ADVANTAGE = "competitive_advantage"


# Core Models
class CustomerProfile(BaseModel):
    """Customer profile information"""
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    age_range: Optional[str] = None
    occupation: Optional[str] = None
    location: Optional[str] = None
    income_range: Optional[str] = None
    company_size: Optional[str] = None
    industry: Optional[str] = None
    segment: Optional[CustomerSegment] = None
    characteristics: List[str] = Field(default_factory=list)
    pain_points: List[str] = Field(default_factory=list)
    goals: List[str] = Field(default_factory=list)
    current_solutions: List[str] = Field(default_factory=list)


class InterviewFile(BaseModel):
    """File associated with an interview"""
    id: str
    file_type: FileType
    file_path: str
    file_size: Optional[int] = None
    duration: Optional[float] = None  # in seconds
    upload_time: datetime = Field(default_factory=datetime.utcnow)
    processed: bool = False
    transcription_id: Optional[str] = None
    

class Transcription(BaseModel):
    """Transcription of audio/video content"""
    id: str
    file_id: str
    content: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    language: str = "en"
    speaker_labels: List[Dict[str, Any]] = Field(default_factory=list)
    timestamps: List[Dict[str, Any]] = Field(default_factory=list)
    processing_time: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ExtractedInsight(BaseModel):
    """AI-extracted insight from interview content"""
    id: str
    interview_id: str
    type: InsightType
    content: str
    quote: str  # Original quote from transcript
    context: str  # Surrounding context
    confidence: ConfidenceLevel
    confidence_score: float = Field(ge=0.0, le=1.0)
    speaker: Optional[str] = None
    timestamp: Optional[float] = None
    tags: List[str] = Field(default_factory=list)
    impact_score: float = Field(ge=0.0, le=10.0)  # Business impact score
    frequency_mentioned: int = 1
    validation_status: str = "pending"  # pending, validated, rejected
    bmc_impact: Optional[Dict[str, Any]] = None  # Which BMC sections to update
    created_at: datetime = Field(default_factory=datetime.utcnow)


class InterviewScore(BaseModel):
    """Scoring for different aspects of the interview"""
    category: ScoreCategory
    score: float = Field(ge=0.0, le=10.0)
    reasoning: str
    supporting_quotes: List[str] = Field(default_factory=list)
    confidence: ConfidenceLevel


class InterviewAnalysis(BaseModel):
    """Complete analysis of an interview"""
    id: str
    interview_id: str
    overall_score: float = Field(ge=0.0, le=10.0)
    category_scores: List[InterviewScore] = Field(default_factory=list)
    key_insights: List[ExtractedInsight] = Field(default_factory=list)
    pain_points: List[str] = Field(default_factory=list)
    validation_points: List[str] = Field(default_factory=list)
    feature_requests: List[str] = Field(default_factory=list)
    competitive_mentions: List[str] = Field(default_factory=list)
    pricing_feedback: List[str] = Field(default_factory=list)
    persona_updates: Dict[str, Any] = Field(default_factory=dict)
    bmc_updates: Dict[str, Any] = Field(default_factory=dict)
    follow_up_questions: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    sentiment_analysis: Dict[str, float] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CustomerInterview(BaseModel):
    """Main interview entity"""
    id: str
    user_id: str
    idea_id: str
    customer_profile: CustomerProfile
    interview_type: InterviewType
    status: InterviewStatus
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None  # in minutes
    platform: Optional[str] = None  # Zoom, Google Meet, etc.
    notes: Optional[str] = None
    files: List[InterviewFile] = Field(default_factory=list)
    transcriptions: List[Transcription] = Field(default_factory=list)
    analysis: Optional[InterviewAnalysis] = None
    follow_up_needed: bool = False
    follow_up_date: Optional[datetime] = None
    follow_up_notes: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SegmentAnalysis(BaseModel):
    """Analysis for a customer segment"""
    segment: CustomerSegment
    total_interviews: int
    average_scores: Dict[str, float] = Field(default_factory=dict)
    common_pain_points: List[Dict[str, Any]] = Field(default_factory=list)
    common_validation_points: List[Dict[str, Any]] = Field(default_factory=list)
    pricing_insights: Dict[str, Any] = Field(default_factory=dict)
    market_size_indicators: List[str] = Field(default_factory=list)
    confidence_level: ConfidenceLevel
    recommendations: List[str] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DiscoveryDashboard(BaseModel):
    """Dashboard metrics and insights"""
    user_id: str
    idea_id: str
    total_interviews: int
    target_interviews: int
    progress_percentage: float
    quality_score: float = Field(ge=0.0, le=10.0)
    validation_score: float = Field(ge=0.0, le=10.0)
    response_rate: float
    avg_duration: float
    problem_confirmation: float
    solution_interest: float
    willingness_to_pay: float
    referral_willingness: float
    risk_level: str
    segment_analyses: List[SegmentAnalysis] = Field(default_factory=list)
    top_insights: List[ExtractedInsight] = Field(default_factory=list)
    opportunities: List[Dict[str, Any]] = Field(default_factory=list)
    risks: List[Dict[str, Any]] = Field(default_factory=list)
    ai_recommendations: List[str] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# API Request/Response Models
class InterviewCreateRequest(BaseModel):
    customer_profile: CustomerProfile
    interview_type: InterviewType
    scheduled_at: Optional[datetime] = None
    platform: Optional[str] = None
    notes: Optional[str] = None
    idea_id: str


class InterviewUpdateRequest(BaseModel):
    status: Optional[InterviewStatus] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None
    follow_up_needed: Optional[bool] = None
    follow_up_date: Optional[datetime] = None
    follow_up_notes: Optional[str] = None
    tags: Optional[List[str]] = None


class FileUploadRequest(BaseModel):
    interview_id: str
    file_type: FileType
    file_name: str


class TranscriptionRequest(BaseModel):
    file_id: str
    language: str = "en"
    enable_speaker_labels: bool = True
    enable_timestamps: bool = True


class AnalysisRequest(BaseModel):
    interview_id: str
    force_reanalysis: bool = False


class InsightValidationRequest(BaseModel):
    insight_id: str
    validation_status: str  # validated, rejected
    notes: Optional[str] = None


class BMCUpdateRequest(BaseModel):
    insight_ids: List[str]
    apply_updates: bool = True
    preview_only: bool = False


# Response Models
class InterviewResponse(BaseModel):
    interview: CustomerInterview
    message: str = "Interview retrieved successfully"


class InterviewListResponse(BaseModel):
    interviews: List[CustomerInterview]
    total: int
    page: int
    per_page: int
    message: str = "Interviews retrieved successfully"


class TranscriptionResponse(BaseModel):
    transcription: Transcription
    message: str = "Transcription completed successfully"


class AnalysisResponse(BaseModel):
    analysis: InterviewAnalysis
    message: str = "Analysis completed successfully"


class DashboardResponse(BaseModel):
    dashboard: DiscoveryDashboard
    message: str = "Dashboard data retrieved successfully"


class InsightResponse(BaseModel):
    insights: List[ExtractedInsight]
    total: int
    message: str = "Insights retrieved successfully"


class BMCUpdateResponse(BaseModel):
    preview: Optional[Dict[str, Any]] = None
    applied_updates: Optional[Dict[str, Any]] = None
    affected_sections: List[str] = Field(default_factory=list)
    message: str = "BMC update processed successfully"


class QuestionGeneratorResponse(BaseModel):
    questions: List[str]
    interview_type: InterviewType
    segment: Optional[CustomerSegment] = None
    context: str
    message: str = "Questions generated successfully" 