from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from core.market_models import (
    GeographicScope, CustomerType, RevenueModel, MarketSizingReport
)


class MarketSizingRequest(BaseModel):
    """Request model for market sizing analysis"""
    business_idea: str = Field(..., description="Detailed business idea description")
    industry: str = Field(..., description="Primary industry or sector")
    target_market: str = Field(..., description="Target market description")
    geographic_scope: GeographicScope = Field(
        default=GeographicScope.USA,
        description="Geographic scope for market analysis"
    )
    custom_geography: Optional[List[str]] = Field(
        None,
        description="Custom geographic regions if scope is CUSTOM"
    )
    customer_type: CustomerType = Field(..., description="Target customer type")
    revenue_model: RevenueModel = Field(..., description="Primary revenue model")
    estimated_price_point: Optional[float] = Field(
        None,
        description="Estimated price per unit/subscription"
    )
    idea_id: Optional[str] = Field(
        None,
        description="Business idea ID for authenticated users to save results"
    )


class MarketSizingResponse(BaseModel):
    """Response model for market sizing analysis"""
    status: str = Field(..., description="Analysis status")
    report: MarketSizingReport = Field(..., description="Comprehensive market sizing report")
    analysis_id: Optional[str] = Field(
        None,
        description="Analysis ID (included when saved for authenticated users)"
    )
    message: str = Field(..., description="Status message")
    execution_time: Optional[float] = Field(None, description="Analysis execution time in seconds")


class MarketSizingHistoryItem(BaseModel):
    """Individual market sizing analysis in history"""
    analysis_id: str = Field(..., description="Analysis ID")
    business_idea: str = Field(..., description="Business idea analyzed")
    industry: str = Field(..., description="Industry")
    tam: float = Field(..., description="Total Addressable Market")
    sam: float = Field(..., description="Serviceable Addressable Market")
    som: float = Field(..., description="Serviceable Obtainable Market")
    confidence_level: str = Field(..., description="Analysis confidence level")
    created_at: datetime = Field(..., description="Analysis creation date")
    has_feedback: bool = Field(default=False, description="Whether analysis has feedback")


class MarketSizingHistory(BaseModel):
    """Market sizing analysis history for a user"""
    total_count: int = Field(..., description="Total number of analyses")
    analyses: List[MarketSizingHistoryItem] = Field(..., description="List of analyses")
    page: int = Field(default=1, description="Current page number")
    per_page: int = Field(default=10, description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")


class MarketOpportunityInsight(BaseModel):
    """Market opportunity insight"""
    title: str = Field(..., description="Insight title")
    description: str = Field(..., description="Detailed description")
    value: float = Field(..., description="Quantified value if applicable")
    confidence: str = Field(..., description="Confidence level")


class MarketOpportunityResponse(BaseModel):
    """Response for market opportunity insights"""
    total_market_value: float = Field(..., description="Total market value analyzed")
    growth_potential: float = Field(..., description="Growth potential percentage")
    key_insights: List[MarketOpportunityInsight] = Field(..., description="Key market insights")
    recommendation: str = Field(..., description="Overall recommendation")
    next_steps: List[str] = Field(..., description="Recommended next steps")


class GeographicOptions(BaseModel):
    """Available geographic scope options"""
    regions: Dict[str, str] = Field(..., description="Available geographic regions")
    popular_combinations: List[List[str]] = Field(..., description="Popular region combinations")


class IndustryBenchmarks(BaseModel):
    """Industry benchmark data"""
    industry: str = Field(..., description="Industry name")
    typical_growth_rate: str = Field(..., description="Typical growth rate range")
    market_concentration: str = Field(..., description="Market concentration level")
    average_tam_size: str = Field(..., description="Average TAM size range")
    key_metrics: Dict[str, str] = Field(..., description="Key industry metrics")


class MarketSizingOptions(BaseModel):
    """Available options for market sizing"""
    geographic_scopes: GeographicOptions = Field(..., description="Geographic options")
    customer_types: Dict[str, str] = Field(..., description="Customer type descriptions")
    revenue_models: Dict[str, str] = Field(..., description="Revenue model descriptions")
    industry_benchmarks: List[IndustryBenchmarks] = Field(..., description="Industry benchmarks")
    pricing_guidelines: Dict[str, str] = Field(..., description="Pricing estimation guidelines") 