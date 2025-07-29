from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class RevenueModelType(str, Enum):
    SUBSCRIPTION = "subscription"
    FREEMIUM = "freemium"
    PREMIUM = "premium"
    ONE_TIME = "one_time_purchase"
    MARKETPLACE = "marketplace_commission"
    SPONSORSHIP = "sponsorship"
    ADVERTISING = "advertising"
    TRANSACTION_FEE = "transaction_fee"
    LICENSING = "licensing"
    CONSULTING = "consulting_services"


class PricingStrategy(str, Enum):
    PENETRATION = "penetration_pricing"
    PREMIUM = "premium_pricing"
    COMPETITIVE = "competitive_pricing"
    VALUE_BASED = "value_based_pricing"
    FREEMIUM = "freemium_pricing"
    TIERED = "tiered_pricing"


class BusinessModelInput(BaseModel):
    business_idea: str = Field(..., description="Business idea description")
    target_market: str = Field(..., description="Target market description")
    industry: str = Field(..., description="Industry vertical")
    estimated_users: Optional[int] = Field(None, description="Estimated number of users/customers")
    development_cost: Optional[float] = Field(None, description="Estimated development/setup costs")
    operational_cost_monthly: Optional[float] = Field(None, description="Monthly operational costs")
    idea_id: Optional[str] = Field(None, description="Associated business idea ID")
    user_id: Optional[str] = Field(None, description="User ID for authenticated requests")


class RevenueModelRecommendation(BaseModel):
    model_type: RevenueModelType
    recommended_price: Optional[float] = None
    price_range: Dict[str, float] = Field(default_factory=dict)  # {"min": 9.99, "max": 49.99}
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)
    suitability_score: float = Field(..., ge=0.0, le=10.0)
    market_examples: List[str] = Field(default_factory=list)
    implementation_complexity: str = Field(..., description="Low, Medium, High")
    time_to_revenue: str = Field(..., description="Immediate, 1-3 months, 3-6 months, 6+ months")


class ProfitabilityProjection(BaseModel):
    monthly_revenue: float
    annual_revenue: float
    monthly_costs: float
    annual_costs: float
    monthly_profit: float
    annual_profit: float
    break_even_months: int
    break_even_users: int
    roi_percentage: float


class PricingInsights(BaseModel):
    recommended_strategy: PricingStrategy
    competitive_price_range: Dict[str, float] = Field(default_factory=dict)
    suggested_pricing_tiers: List[Dict[str, Any]] = Field(default_factory=list)
    price_elasticity_insights: List[str] = Field(default_factory=list)
    optimization_recommendations: List[str] = Field(default_factory=list)


class MarketBenchmarks(BaseModel):
    industry_cac: Optional[float] = Field(None, description="Customer Acquisition Cost")
    industry_ltv: Optional[float] = Field(None, description="Customer Lifetime Value")
    ltv_cac_ratio: Optional[float] = Field(None, description="LTV:CAC ratio")
    industry_churn_rate: Optional[float] = Field(None, description="Monthly churn rate")
    average_revenue_per_user: Optional[float] = Field(None, description="ARPU")
    market_growth_rate: Optional[float] = Field(None, description="Market growth rate")
    competitive_landscape_summary: str = Field(default="", description="Summary of competitive landscape")


class BusinessModelReport(BaseModel):
    business_idea: str
    analysis_date: datetime = Field(default_factory=datetime.utcnow)
    
    # Core recommendations
    recommended_revenue_models: List[RevenueModelRecommendation]
    primary_recommendation: RevenueModelRecommendation
    
    # Financial projections
    profitability_projections: List[ProfitabilityProjection]  # Different scenarios
    
    # Pricing strategy
    pricing_insights: PricingInsights
    
    # Market data
    market_benchmarks: MarketBenchmarks
    
    # Context from other analyses
    competitive_context: Optional[Dict[str, Any]] = None
    persona_context: Optional[Dict[str, Any]] = None
    market_sizing_context: Optional[Dict[str, Any]] = None
    
    # Implementation guidance
    implementation_roadmap: List[str] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)
    success_metrics: List[str] = Field(default_factory=list)
    
    # Execution details
    execution_time: Optional[float] = None


class BusinessModelState(BaseModel):
    """State model for business model analysis workflow"""
    business_input: BusinessModelInput
    competitive_context: Optional[Dict[str, Any]] = None
    persona_context: Optional[Dict[str, Any]] = None
    market_sizing_context: Optional[Dict[str, Any]] = None
    revenue_recommendations: List[RevenueModelRecommendation] = Field(default_factory=list)
    profitability_projections: List[ProfitabilityProjection] = Field(default_factory=list)
    pricing_insights: Optional[PricingInsights] = None
    market_benchmarks: Optional[MarketBenchmarks] = None
    final_report: Optional[BusinessModelReport] = None
    errors: List[str] = Field(default_factory=list)


# API Request/Response models
class BusinessModelRequest(BaseModel):
    idea_id: str = Field(..., description="Business idea ID to analyze", example="550e8400-e29b-41d4-a716-446655440000")


class BusinessModelResponse(BaseModel):
    report: BusinessModelReport
    analysis_id: Optional[str] = None
    message: str = "Business model analysis completed successfully"


class BusinessModelHistoryItem(BaseModel):
    id: str
    business_idea: str
    primary_revenue_model: str
    projected_monthly_revenue: float
    break_even_months: int
    created_at: datetime


class BusinessModelHistory(BaseModel):
    analyses: List[BusinessModelHistoryItem]
    total_count: int
    page: int
    per_page: int
    total_pages: int


class BusinessModelOptions(BaseModel):
    revenue_models: List[Dict[str, str]]
    pricing_strategies: List[Dict[str, str]]
    industries: List[str]
    cost_categories: List[str]


class RevenueModelComparison(BaseModel):
    business_idea: str
    model_comparisons: List[RevenueModelRecommendation]
    recommendation_summary: str 