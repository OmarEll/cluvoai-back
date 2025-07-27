from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class CustomerSegmentType(str, Enum):
    MASS_MARKET = "mass_market"
    NICHE_MARKET = "niche_market"
    SEGMENTED = "segmented"
    DIVERSIFIED = "diversified"
    MULTI_SIDED_PLATFORM = "multi_sided_platform"


class ValuePropositionType(str, Enum):
    NEWNESS = "newness"
    PERFORMANCE = "performance"
    CUSTOMIZATION = "customization"
    GETTING_JOB_DONE = "getting_job_done"
    DESIGN = "design"
    BRAND_STATUS = "brand_status"
    PRICE = "price"
    COST_REDUCTION = "cost_reduction"
    RISK_REDUCTION = "risk_reduction"
    ACCESSIBILITY = "accessibility"
    CONVENIENCE = "convenience"


class ChannelType(str, Enum):
    OWN_CHANNELS = "own_channels"
    PARTNER_CHANNELS = "partner_channels"
    HYBRID = "hybrid"


class CustomerRelationshipType(str, Enum):
    PERSONAL_ASSISTANCE = "personal_assistance"
    DEDICATED_PERSONAL_ASSISTANCE = "dedicated_personal_assistance"
    SELF_SERVICE = "self_service"
    AUTOMATED_SERVICES = "automated_services"
    COMMUNITIES = "communities"
    CO_CREATION = "co_creation"


class RevenueStreamType(str, Enum):
    ASSET_SALE = "asset_sale"
    USAGE_FEE = "usage_fee"
    SUBSCRIPTION_FEES = "subscription_fees"
    LENDING_LEASING_RENTING = "lending_leasing_renting"
    LICENSING = "licensing"
    BROKERAGE_FEES = "brokerage_fees"
    ADVERTISING = "advertising"


class KeyResourceType(str, Enum):
    PHYSICAL = "physical"
    INTELLECTUAL = "intellectual"
    HUMAN = "human"
    FINANCIAL = "financial"


class KeyActivityType(str, Enum):
    PRODUCTION = "production"
    PROBLEM_SOLVING = "problem_solving"
    PLATFORM_NETWORK = "platform_network"


class PartnershipType(str, Enum):
    STRATEGIC_ALLIANCES = "strategic_alliances"
    COOPETITION = "coopetition"
    JOINT_VENTURES = "joint_ventures"
    BUYER_SUPPLIER = "buyer_supplier"


class CostStructureType(str, Enum):
    COST_DRIVEN = "cost_driven"
    VALUE_DRIVEN = "value_driven"


# Canvas Building Blocks
class CustomerSegments(BaseModel):
    """Customer Segments building block"""
    segment_type: CustomerSegmentType
    description: str
    characteristics: List[str] = Field(default_factory=list)
    needs: List[str] = Field(default_factory=list)
    size_estimate: Optional[str] = None
    persona_insights: Optional[Dict[str, Any]] = None  # From persona analysis


class ValuePropositions(BaseModel):
    """Value Propositions building block"""
    proposition_type: ValuePropositionType
    description: str
    benefits: List[str] = Field(default_factory=list)
    pain_points_solved: List[str] = Field(default_factory=list)
    competitive_advantages: List[str] = Field(default_factory=list)
    quantifiable_value: Optional[str] = None
    competitive_insights: Optional[Dict[str, Any]] = None  # From competitor analysis


class Channels(BaseModel):
    """Channels building block"""
    channel_type: ChannelType
    description: str
    touchpoints: List[str] = Field(default_factory=list)
    effectiveness_metrics: List[str] = Field(default_factory=list)
    cost_implications: Optional[str] = None
    market_reach: Optional[str] = None


class CustomerRelationships(BaseModel):
    """Customer Relationships building block"""
    relationship_type: CustomerRelationshipType
    description: str
    acquisition_strategy: str
    retention_strategy: str
    growth_strategy: str
    automation_level: Optional[str] = None
    personalization_degree: Optional[str] = None


class RevenueStreams(BaseModel):
    """Revenue Streams building block"""
    stream_type: RevenueStreamType
    description: str
    pricing_model: str
    revenue_potential: Optional[str] = None
    pricing_strategy: Optional[str] = None
    market_benchmarks: Optional[Dict[str, Any]] = None  # From market sizing
    business_model_insights: Optional[Dict[str, Any]] = None  # From business model analysis


class KeyResources(BaseModel):
    """Key Resources building block"""
    resource_type: KeyResourceType
    description: str
    importance_level: str  # Critical, Important, Nice to have
    acquisition_strategy: Optional[str] = None
    cost_implications: Optional[str] = None
    competitive_advantage: Optional[str] = None


class KeyActivities(BaseModel):
    """Key Activities building block"""
    activity_type: KeyActivityType
    description: str
    criticality: str  # Critical, Important, Supporting
    resource_requirements: List[str] = Field(default_factory=list)
    efficiency_metrics: List[str] = Field(default_factory=list)
    automation_potential: Optional[str] = None


class KeyPartnerships(BaseModel):
    """Key Partnerships building block"""
    partnership_type: PartnershipType
    description: str
    partner_categories: List[str] = Field(default_factory=list)
    value_provided: List[str] = Field(default_factory=list)
    risks_and_mitigation: List[str] = Field(default_factory=list)
    competitive_insights: Optional[Dict[str, Any]] = None  # From competitor analysis


class CostStructure(BaseModel):
    """Cost Structure building block"""
    structure_type: CostStructureType
    description: str
    fixed_costs: List[str] = Field(default_factory=list)
    variable_costs: List[str] = Field(default_factory=list)
    cost_drivers: List[str] = Field(default_factory=list)
    optimization_opportunities: List[str] = Field(default_factory=list)
    profitability_insights: Optional[Dict[str, Any]] = None  # From business model analysis


class BusinessModelCanvas(BaseModel):
    """Complete Business Model Canvas"""
    id: Optional[str] = None
    business_idea: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # The nine building blocks
    customer_segments: CustomerSegments
    value_propositions: ValuePropositions
    channels: Channels
    customer_relationships: CustomerRelationships
    revenue_streams: RevenueStreams
    key_resources: KeyResources
    key_activities: KeyActivities
    key_partnerships: KeyPartnerships
    cost_structure: CostStructure
    
    # Context from previous analyses
    competitive_context: Optional[Dict[str, Any]] = None
    persona_context: Optional[Dict[str, Any]] = None
    market_sizing_context: Optional[Dict[str, Any]] = None
    business_model_context: Optional[Dict[str, Any]] = None
    
    # Canvas metadata
    version: str = "1.0"
    status: str = "draft"  # draft, reviewed, finalized
    notes: Optional[str] = None
    execution_time: Optional[float] = None


# API Request/Response models
class BusinessModelCanvasRequest(BaseModel):
    business_idea: str
    target_market: str
    industry: str
    idea_id: Optional[str] = None
    user_id: Optional[str] = None


class BusinessModelCanvasResponse(BaseModel):
    canvas: BusinessModelCanvas
    analysis_id: Optional[str] = None
    idea_id: Optional[str] = None
    message: str = "Business Model Canvas generated successfully"


class CanvasUpdateRequest(BaseModel):
    """Request for updating specific canvas building blocks"""
    building_block: str  # e.g., "customer_segments", "value_propositions"
    updates: Dict[str, Any]


class CanvasVersion(BaseModel):
    """Canvas version for multiple iterations"""
    version_id: str
    canvas: BusinessModelCanvas
    created_at: datetime
    changes_description: Optional[str] = None


class BusinessModelCanvasHistory(BaseModel):
    """History of canvas versions"""
    idea_id: str
    versions: List[CanvasVersion]
    total_versions: int
    latest_version: str


class CanvasInsights(BaseModel):
    """AI-generated insights for canvas optimization"""
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)
    threats: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    risk_assessment: Dict[str, str] = Field(default_factory=dict)
    optimization_suggestions: List[str] = Field(default_factory=list)


class CanvasExportFormat(str, Enum):
    PDF = "pdf"
    JSON = "json"
    CSV = "csv"
    VISUAL = "visual"


class CanvasExportRequest(BaseModel):
    format: CanvasExportFormat
    include_insights: bool = True
    include_context: bool = True 