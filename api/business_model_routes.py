from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List

from core.business_model_models import (
    BusinessModelRequest, BusinessModelResponse, BusinessModelInput,
    BusinessModelHistory, BusinessModelOptions, RevenueModelComparison
)
from core.analysis_models import AnalysisType
from services.auth_service import auth_service
from services.analysis_storage_service import analysis_storage_service
from workflows.business_model_workflow import business_model_workflow
from api.auth_routes import security

router = APIRouter(prefix="/business-model", tags=["Business Model Analysis"])


async def get_current_user_email(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Dependency to get current user's email from JWT token"""
    token_data = auth_service.verify_token(credentials.credentials)
    return token_data.email


@router.post("/analyze", response_model=BusinessModelResponse)
async def analyze_business_model(
    request: BusinessModelRequest,
    user_email: str = Depends(get_current_user_email)
):
    """
    Generate comprehensive business model analysis with intelligent context from previous analyses
    
    This endpoint leverages:
    - Competitive analysis for pricing intelligence and market positioning
    - Persona analysis for customer willingness to pay and preferences  
    - Market sizing for revenue projections and market benchmarks
    """
    try:
        print(f"🚀 Starting business model analysis for user: {user_email}")
        
        # Create business model input
        business_input = BusinessModelInput(
            business_idea=request.business_idea,
            target_market=request.target_market,
            industry=request.industry,
            estimated_users=request.estimated_users,
            development_cost=request.development_cost,
            operational_cost_monthly=request.operational_cost_monthly,
            idea_id=request.idea_id,
            user_id=user_email
        )
        
        # Run comprehensive business model analysis
        report = await business_model_workflow.run_analysis(business_input)
        
        # Save analysis to database if user is authenticated and idea_id is provided
        analysis_id = None
        if request.idea_id:
            try:
                saved_analysis = await analysis_storage_service.save_analysis_result(
                    user_id=user_email,
                    idea_id=request.idea_id,
                    analysis_type=AnalysisType.BUSINESS_MODEL,
                    business_model_report=report,
                    execution_time=report.execution_time
                )
                analysis_id = saved_analysis.id
                print(f"✅ Business model analysis saved with ID: {analysis_id}")
                
            except Exception as e:
                print(f"Warning: Failed to save business model analysis: {e}")
        
        return BusinessModelResponse(
            report=report,
            analysis_id=analysis_id,
            message="Business model analysis completed successfully with intelligent context from previous analyses"
        )
        
    except Exception as e:
        print(f"Error in business model analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Business model analysis failed: {str(e)}"
        )


@router.get("/analyze/{idea_id}", response_model=BusinessModelResponse)
async def get_saved_business_model_analysis(
    idea_id: str,
    user_email: str = Depends(get_current_user_email)
):
    """
    Retrieve saved business model analysis for a specific business idea
    """
    try:
        # Get saved analysis
        saved_analysis = await analysis_storage_service.get_user_analysis(
            user_email, idea_id, AnalysisType.BUSINESS_MODEL, include_feedback=True
        )
        
        if not saved_analysis or not saved_analysis.business_model_report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business model analysis not found for this idea"
            )
        
        return BusinessModelResponse(
            report=saved_analysis.business_model_report,
            analysis_id=saved_analysis.id,
            message="Business model analysis retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error retrieving business model analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve business model analysis: {str(e)}"
        )


@router.get("/history", response_model=BusinessModelHistory)
async def get_business_model_history(
    user_email: str = Depends(get_current_user_email),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=50, description="Items per page")
):
    """
    Get user's business model analysis history with pagination
    """
    try:
        # Get user's business model analyses
        history_data = await analysis_storage_service.get_user_analyses_history(
            user_email, AnalysisType.BUSINESS_MODEL, page, per_page
        )
        
        # Transform to business model history format
        history_items = []
        for analysis in history_data["analyses"]:
            if analysis.get("business_model_report"):
                report = analysis["business_model_report"]
                primary_rec = report.get("primary_recommendation", {})
                
                # Extract revenue projection from the realistic scenario
                projections = report.get("profitability_projections", [])
                monthly_revenue = 0
                break_even_months = 12
                
                if projections:
                    # Use realistic scenario (middle projection)
                    realistic_proj = projections[1] if len(projections) > 1 else projections[0]
                    monthly_revenue = realistic_proj.get("monthly_revenue", 0)
                    break_even_months = realistic_proj.get("break_even_months", 12)
                
                history_items.append({
                    "id": analysis["id"],
                    "business_idea": report.get("business_idea", ""),
                    "primary_revenue_model": primary_rec.get("model_type", "subscription"),
                    "projected_monthly_revenue": monthly_revenue,
                    "break_even_months": break_even_months,
                    "created_at": analysis["created_at"]
                })
        
        return BusinessModelHistory(
            analyses=history_items,
            total_count=history_data["total_count"],
            page=history_data["page"],
            per_page=history_data["per_page"],
            total_pages=history_data["total_pages"]
        )
        
    except Exception as e:
        print(f"Error getting business model history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve business model history: {str(e)}"
        )


@router.get("/compare-models/{idea_id}", response_model=RevenueModelComparison)
async def compare_revenue_models(
    idea_id: str,
    user_email: str = Depends(get_current_user_email)
):
    """
    Compare different revenue models for a specific business idea using competitive and persona intelligence
    """
    try:
        # Get saved business model analysis
        saved_analysis = await analysis_storage_service.get_user_analysis(
            user_email, idea_id, AnalysisType.BUSINESS_MODEL, include_feedback=False
        )
        
        if not saved_analysis or not saved_analysis.business_model_report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business model analysis not found. Please run analysis first."
            )
        
        report = saved_analysis.business_model_report
        
        return RevenueModelComparison(
            business_idea=report.business_idea,
            model_comparisons=report.recommended_revenue_models,
            recommendation_summary=f"Based on competitive intelligence and persona analysis, "
                                  f"{report.primary_recommendation.model_type.value} model is recommended "
                                  f"with a suitability score of {report.primary_recommendation.suitability_score:.1f}/10"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error comparing revenue models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare revenue models: {str(e)}"
        )


@router.get("/options", response_model=BusinessModelOptions)
async def get_business_model_options():
    """
    Get available options for business model analysis
    """
    return BusinessModelOptions(
        revenue_models=[
            {"value": "subscription", "label": "Subscription (Recurring Revenue)"},
            {"value": "freemium", "label": "Freemium (Free + Premium Tiers)"},
            {"value": "premium", "label": "Premium (High-Value Offering)"},
            {"value": "one_time_purchase", "label": "One-Time Purchase"},
            {"value": "marketplace_commission", "label": "Marketplace Commission"},
            {"value": "sponsorship", "label": "Sponsorship/Advertising"},
            {"value": "transaction_fee", "label": "Transaction Fees"},
            {"value": "licensing", "label": "Licensing"},
            {"value": "consulting_services", "label": "Consulting Services"}
        ],
        pricing_strategies=[
            {"value": "penetration_pricing", "label": "Penetration Pricing (Low initial price)"},
            {"value": "premium_pricing", "label": "Premium Pricing (High-value positioning)"},
            {"value": "competitive_pricing", "label": "Competitive Pricing (Market-based)"},
            {"value": "value_based_pricing", "label": "Value-Based Pricing (Customer value)"},
            {"value": "freemium_pricing", "label": "Freemium Pricing (Free + Paid tiers)"},
            {"value": "tiered_pricing", "label": "Tiered Pricing (Multiple price points)"}
        ],
        industries=[
            "Software/SaaS", "E-commerce", "Healthcare", "Education", "Finance",
            "Marketing", "Manufacturing", "Consulting", "Media", "Real Estate",
            "Food & Beverage", "Transportation", "Energy", "Retail", "Other"
        ],
        cost_categories=[
            "Development/Setup Costs", "Monthly Operational Costs", "Marketing/Customer Acquisition",
            "Personnel/Salaries", "Infrastructure/Hosting", "Legal/Compliance",
            "Research & Development", "Sales & Distribution", "Support & Maintenance"
        ]
    )


@router.get("/insights/{idea_id}")
async def get_business_model_insights(
    idea_id: str,
    user_email: str = Depends(get_current_user_email)
):
    """
    Get actionable business model insights by combining analysis results with competitive and persona intelligence
    """
    try:
        # Get business model analysis
        business_model_analysis = await analysis_storage_service.get_user_analysis(
            user_email, idea_id, AnalysisType.BUSINESS_MODEL, include_feedback=False
        )
        
        if not business_model_analysis or not business_model_analysis.business_model_report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business model analysis not found"
            )
        
        report = business_model_analysis.business_model_report
        
        # Generate actionable insights
        insights = {
            "revenue_model_recommendation": {
                "primary_model": report.primary_recommendation.model_type.value,
                "confidence_score": report.primary_recommendation.suitability_score,
                "key_advantages": report.primary_recommendation.pros[:3],
                "potential_risks": report.primary_recommendation.cons[:2]
            },
            "pricing_strategy": {
                "recommended_strategy": report.pricing_insights.recommended_strategy.value,
                "suggested_price_range": report.pricing_insights.competitive_price_range,
                "optimization_tips": report.pricing_insights.optimization_recommendations[:3]
            },
            "profitability_outlook": {
                "scenarios": len(report.profitability_projections),
                "realistic_monthly_revenue": report.profitability_projections[1].monthly_revenue if len(report.profitability_projections) > 1 else 0,
                "break_even_timeline": f"{report.profitability_projections[1].break_even_months} months" if len(report.profitability_projections) > 1 else "Unknown",
                "roi_projection": f"{report.profitability_projections[1].roi_percentage:.1f}%" if len(report.profitability_projections) > 1 else "0%"
            },
            "market_benchmarks": {
                "industry_cac": report.market_benchmarks.industry_cac,
                "industry_ltv": report.market_benchmarks.industry_ltv,
                "ltv_cac_ratio": report.market_benchmarks.ltv_cac_ratio,
                "competitive_landscape": report.market_benchmarks.competitive_landscape_summary
            },
            "implementation_guidance": {
                "next_steps": report.implementation_roadmap[:3],
                "success_metrics": report.success_metrics[:4],
                "key_risks": report.risk_factors[:3]
            },
            "contextual_intelligence": {
                "competitive_context_used": bool(report.competitive_context),
                "persona_context_used": bool(report.persona_context),
                "market_sizing_context_used": bool(report.market_sizing_context),
                "cross_analysis_benefits": [
                    "Pricing informed by competitive intelligence",
                    "Revenue projections based on persona insights",
                    "Market benchmarks from comprehensive analysis"
                ]
            }
        }
        
        return insights
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting business model insights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get business model insights: {str(e)}"
        ) 