from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class PersonaDemographic(BaseModel):
    age_range: str = Field(..., description="Age range (e.g., '25-35')")
    gender: Optional[str] = Field(None, description="Primary gender")
    location: Optional[str] = Field(None, description="Geographic location")
    income_range: Optional[str] = Field(None, description="Income bracket")


class ProfessionalDetails(BaseModel):
    job_title: Optional[str] = Field(None, description="Job title or role")
    industry: Optional[str] = Field(None, description="Industry vertical")
    company_size: Optional[str] = Field(None, description="Company size preference")
    experience_level: Optional[str] = Field(None, description="Years of experience")


class PersonaPsychographics(BaseModel):
    goals: List[str] = Field(default_factory=list, description="Primary goals and motivations")
    pain_points: List[str] = Field(default_factory=list, description="Key challenges and frustrations")
    motivations: List[str] = Field(default_factory=list, description="What drives their decisions")
    buying_behavior: List[str] = Field(default_factory=list, description="How they make purchasing decisions")


class TechHabits(BaseModel):
    preferred_platforms: List[str] = Field(default_factory=list, description="Social media platforms they use")
    device_usage: List[str] = Field(default_factory=list, description="Devices they prefer")
    software_tools: List[str] = Field(default_factory=list, description="Software and tools they use")
    content_consumption: List[str] = Field(default_factory=list, description="Types of content they consume")


class PersonaInsights(BaseModel):
    market_size: Optional[str] = Field(None, description="Estimated market size for this persona")
    competitor_targeting: List[str] = Field(default_factory=list, description="How competitors target this persona")
    gaps_identified: List[str] = Field(default_factory=list, description="Gaps in current market offerings")
    engagement_opportunities: List[str] = Field(default_factory=list, description="Best ways to reach this persona")


class PainPointAnalysis(BaseModel):
    problem_description: str = Field(..., description="Description of the pain point")
    frequency: str = Field(..., description="How often this problem occurs")
    severity: int = Field(..., ge=1, le=10, description="Pain severity score (1-10)")
    current_solutions: List[str] = Field(default_factory=list, description="Current ways they solve this")
    value_proposition_opportunity: str = Field(..., description="How your product could address this")


class TargetPersona(BaseModel):
    name: str = Field(..., description="Persona name (e.g., 'Tech-Savvy Manager')")
    description: str = Field(..., description="Brief persona description")
    demographics: PersonaDemographic
    professional_details: ProfessionalDetails
    psychographics: PersonaPsychographics
    tech_habits: TechHabits
    pain_points_analysis: List[PainPointAnalysis] = Field(default_factory=list)
    persona_insights: PersonaInsights
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Data confidence level")


class PersonaAnalysisInput(BaseModel):
    business_idea: str = Field(..., description="The business idea or product")
    target_market: Optional[str] = Field(None, description="Target market description")
    industry: Optional[str] = Field(None, description="Industry vertical")
    geographic_focus: Optional[str] = Field(None, description="Geographic markets")
    product_category: Optional[str] = Field(None, description="Product category")


class PersonaReport(BaseModel):
    business_idea: str
    total_personas: int
    personas: List[TargetPersona]
    market_insights: List[str] = Field(default_factory=list)
    targeting_recommendations: List[str] = Field(default_factory=list)
    content_strategy_recommendations: List[str] = Field(default_factory=list)
    execution_time: float = 0.0


class PersonaAnalysisState(BaseModel):
    """State model for LangGraph persona analysis workflow"""
    analysis_input: PersonaAnalysisInput
    social_media_data: Dict[str, Any] = Field(default_factory=dict)
    market_research_data: Dict[str, Any] = Field(default_factory=dict)
    generated_personas: List[TargetPersona] = Field(default_factory=list)
    final_report: Optional[PersonaReport] = None
    errors: List[str] = Field(default_factory=list)
    
    # Enhanced with competitor context
    competitor_context: Optional[Dict[str, Any]] = Field(None, description="Competitor analysis context for enhanced persona generation")
    user_id: Optional[str] = Field(None, description="User ID for accessing saved analyses")
    idea_id: Optional[str] = Field(None, description="Business idea ID for accessing saved analyses")