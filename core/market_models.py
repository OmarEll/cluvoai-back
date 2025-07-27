from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class GeographicScope(str, Enum):
    GLOBAL = "global"
    NORTH_AMERICA = "north_america"
    USA = "usa"
    CANADA = "canada"
    EUROPE = "europe"
    ASIA_PACIFIC = "asia_pacific"
    LATIN_AMERICA = "latin_america"
    MIDDLE_EAST_AFRICA = "middle_east_africa"
    CUSTOM = "custom"


class CustomerType(str, Enum):
    B2B = "b2b"
    B2C = "b2c"
    B2B2C = "b2b2c"
    MIXED = "mixed"


class RevenueModel(str, Enum):
    SUBSCRIPTION = "subscription"
    ONE_TIME_PURCHASE = "one_time_purchase"
    FREEMIUM = "freemium"
    MARKETPLACE = "marketplace"
    ADVERTISING = "advertising"
    TRANSACTION_FEE = "transaction_fee"
    LICENSING = "licensing"
    MIXED = "mixed"


class MarketSizingInput(BaseModel):
    """Input model for market sizing analysis"""
    business_idea: str = Field(..., description="Business idea description")
    industry: str = Field(..., description="Primary industry")
    target_market: str = Field(..., description="Target market description")
    geographic_scope: GeographicScope = Field(default=GeographicScope.USA, description="Geographic scope")
    custom_geography: Optional[List[str]] = Field(None, description="Custom geographic regions if scope is CUSTOM")
    customer_type: CustomerType = Field(..., description="Type of customers")
    revenue_model: RevenueModel = Field(..., description="Primary revenue model")
    estimated_price_point: Optional[float] = Field(None, description="Estimated price per unit/subscription")
    idea_id: Optional[str] = Field(None, description="Business idea ID for authenticated users")
    user_id: Optional[str] = Field(None, description="User ID for authenticated users")


class MarketSegment(BaseModel):
    """Individual market segment"""
    name: str = Field(..., description="Segment name")
    size: float = Field(..., description="Market size in USD")
    growth_rate: float = Field(..., description="Annual growth rate as percentage")
    demographics: Dict[str, Any] = Field(default_factory=dict, description="Demographic breakdown")
    characteristics: List[str] = Field(default_factory=list, description="Key characteristics")


class TAMSAMSOMBreakdown(BaseModel):
    """TAM/SAM/SOM market size breakdown"""
    tam: float = Field(..., description="Total Addressable Market in USD")
    tam_description: str = Field(..., description="TAM calculation methodology")
    sam: float = Field(..., description="Serviceable Addressable Market in USD")
    sam_description: str = Field(..., description="SAM calculation methodology")
    som: float = Field(..., description="Serviceable Obtainable Market in USD")
    som_description: str = Field(..., description="SOM calculation methodology")
    market_penetration_rate: float = Field(..., description="Expected market penetration rate")


class MarketTrends(BaseModel):
    """Market trends and growth drivers"""
    growth_drivers: List[str] = Field(default_factory=list, description="Key growth drivers")
    market_challenges: List[str] = Field(default_factory=list, description="Market challenges")
    emerging_trends: List[str] = Field(default_factory=list, description="Emerging trends")
    technology_impact: List[str] = Field(default_factory=list, description="Technology impact factors")
    regulatory_factors: List[str] = Field(default_factory=list, description="Regulatory considerations")


class CompetitivePosition(BaseModel):
    """Competitive positioning in the market"""
    market_gaps: List[str] = Field(default_factory=list, description="Identified market gaps")
    competitive_advantages: List[str] = Field(default_factory=list, description="Potential competitive advantages")
    barrier_to_entry: List[str] = Field(default_factory=list, description="Barriers to entry")
    key_success_factors: List[str] = Field(default_factory=list, description="Key success factors")


class RevenueProjection(BaseModel):
    """Revenue projection model"""
    year: int = Field(..., description="Projection year")
    projected_customers: int = Field(..., description="Projected number of customers")
    average_revenue_per_customer: float = Field(..., description="Average revenue per customer")
    total_revenue: float = Field(..., description="Total projected revenue")
    market_share: float = Field(..., description="Projected market share percentage")


class GeographicBreakdown(BaseModel):
    """Geographic market breakdown"""
    region: str = Field(..., description="Geographic region")
    market_size: float = Field(..., description="Market size in USD")
    potential_customers: int = Field(..., description="Potential customers in region")
    market_maturity: str = Field(..., description="Market maturity level")
    entry_difficulty: str = Field(..., description="Market entry difficulty")


class MarketData(BaseModel):
    """Comprehensive market data"""
    industry_overview: str = Field(..., description="Industry overview")
    market_size_current: float = Field(..., description="Current total market size")
    market_growth_rate: float = Field(..., description="Historical growth rate")
    projected_growth_rate: float = Field(..., description="Projected growth rate")
    data_sources: List[str] = Field(default_factory=list, description="Data sources used")
    confidence_score: float = Field(..., description="Confidence score of data (0-1)")
    last_updated: datetime = Field(default_factory=datetime.now, description="Data last updated")


class MarketSizingReport(BaseModel):
    """Complete market sizing analysis report"""
    executive_summary: str = Field(..., description="Executive summary")
    market_overview: MarketData = Field(..., description="Overall market data")
    tam_sam_som: TAMSAMSOMBreakdown = Field(..., description="TAM/SAM/SOM breakdown")
    market_segments: List[MarketSegment] = Field(default_factory=list, description="Market segments")
    geographic_breakdown: List[GeographicBreakdown] = Field(default_factory=list, description="Geographic analysis")
    market_trends: MarketTrends = Field(..., description="Market trends and drivers")
    competitive_position: CompetitivePosition = Field(..., description="Competitive positioning")
    revenue_projections: List[RevenueProjection] = Field(default_factory=list, description="5-year revenue projections")
    investment_highlights: List[str] = Field(default_factory=list, description="Key investment highlights")
    risk_factors: List[str] = Field(default_factory=list, description="Risk factors")
    recommendations: List[str] = Field(default_factory=list, description="Strategic recommendations")
    methodology: str = Field(..., description="Analysis methodology")
    confidence_level: str = Field(..., description="Overall confidence level")
    generated_at: datetime = Field(default_factory=datetime.now, description="Report generation time")


class MarketSizingState(BaseModel):
    """State model for market sizing workflow"""
    analysis_input: MarketSizingInput
    market_data: Optional[MarketData] = None
    competitor_context: Optional[Dict[str, Any]] = None
    persona_context: Optional[Dict[str, Any]] = None
    industry_research: Optional[Dict[str, Any]] = None
    web_scraped_data: Optional[Dict[str, Any]] = None
    final_report: Optional[MarketSizingReport] = None
    errors: List[str] = Field(default_factory=list)
    user_id: Optional[str] = None
    idea_id: Optional[str] = None 