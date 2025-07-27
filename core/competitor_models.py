from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class CompetitorType(str, Enum):
    DIRECT = "direct"
    INDIRECT = "indirect"
    SUBSTITUTE = "substitute"


class DataSource(str, Enum):
    CRUNCHBASE = "crunchbase"
    LINKEDIN = "linkedin"
    COMPANY_WEBSITE = "company_website"
    SOCIAL_MEDIA = "social_media"
    AI_ESTIMATION = "ai_estimation"


class BusinessInput(BaseModel):
    idea_description: str = Field(..., description="Core business idea")
    target_market: Optional[str] = Field(None, description="Target customer segment")
    business_model: Optional[str] = Field(None, description="Revenue model")
    geographic_focus: Optional[str] = Field(None, description="Target markets")
    industry: Optional[str] = Field(None, description="Industry vertical")


class CompetitorBasic(BaseModel):
    name: str
    domain: Optional[str] = None
    type: CompetitorType = CompetitorType.DIRECT
    description: Optional[str] = None


class FinancialData(BaseModel):
    funding_total: Optional[str] = None
    last_funding_round: Optional[str] = None
    employee_count: Optional[int] = None
    valuation: Optional[str] = None
    founded_year: Optional[int] = None
    location: Optional[str] = None
    industries: List[str] = Field(default_factory=list)
    source: DataSource = DataSource.AI_ESTIMATION


class PricingData(BaseModel):
    monthly_price: Optional[float] = None
    pricing_model: Optional[str] = None
    free_tier: bool = False
    pricing_details: List[str] = Field(default_factory=list)
    source: DataSource = DataSource.AI_ESTIMATION


class MarketSentiment(BaseModel):
    overall_score: float = Field(default=0.0, ge=-1.0, le=1.0)
    reddit_mentions: int = 0
    twitter_mentions: int = 0
    review_score: Optional[float] = None
    key_complaints: List[str] = Field(default_factory=list)
    key_praises: List[str] = Field(default_factory=list)


class CompetitorAnalysis(BaseModel):
    basic_info: CompetitorBasic
    financial_data: FinancialData
    pricing_data: PricingData
    market_sentiment: MarketSentiment = Field(default_factory=lambda: MarketSentiment(overall_score=0.0))
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)
    threats: List[str] = Field(default_factory=list)


class MarketGap(BaseModel):
    category: str
    description: str
    opportunity_score: float = Field(ge=0.0, le=10.0)
    recommended_action: str


class CompetitorReport(BaseModel):
    business_idea: str
    total_competitors: int
    competitors: List[CompetitorAnalysis]
    market_gaps: List[MarketGap]
    key_insights: List[str]
    positioning_recommendations: List[str]
    execution_time: float


class AnalysisState(BaseModel):
    """State model for LangGraph workflow"""
    business_input: BusinessInput
    discovered_competitors: List[CompetitorBasic] = Field(default_factory=list)
    competitor_analyses: List[CompetitorAnalysis] = Field(default_factory=list)
    market_gaps: List[MarketGap] = Field(default_factory=list)
    final_report: Optional[CompetitorReport] = None
    errors: List[str] = Field(default_factory=list)