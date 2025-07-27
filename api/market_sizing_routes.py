import time
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer

from api.market_sizing_schemas import (
    MarketSizingRequest, MarketSizingResponse, MarketSizingHistory,
    MarketOpportunityResponse, MarketSizingOptions
)
from core.market_models import MarketSizingInput, GeographicScope, CustomerType, RevenueModel
from core.analysis_models import AnalysisType
from workflows.simple_market_sizing_workflow import simple_market_sizing_workflow
from services.auth_service import auth_service
from services.user_management_service import user_management_service
from services.analysis_storage_service import analysis_storage_service
from services.feedback_service import feedback_service

router = APIRouter(prefix="/api/v1/market-sizing", tags=["Market Sizing"])
security = HTTPBearer(auto_error=False)


@router.post("/analyze", response_model=MarketSizingResponse)
async def analyze_market_sizing(
    request: MarketSizingRequest,
    authorization: Optional[str] = Depends(security)
):
    """
    Perform comprehensive market sizing analysis with TAM/SAM/SOM calculations
    """
    start_time = time.time()
    
    try:
        # Check for authentication
        user_email = None
        user = None
        
        if authorization:
            try:
                user_email = await auth_service.get_current_user_email(authorization.credentials)
                user = await auth_service.get_user_by_email(user_email)
            except Exception as e:
                print(f"Authentication failed: {e}")
                # Continue without authentication
        
        # Create market sizing input
        market_input = MarketSizingInput(
            business_idea=request.business_idea,
            industry=request.industry,
            target_market=request.target_market,
            geographic_scope=request.geographic_scope,
            custom_geography=request.custom_geography,
            customer_type=request.customer_type,
            revenue_model=request.revenue_model,
            estimated_price_point=request.estimated_price_point,
            idea_id=request.idea_id
        )
        
        # Add user context for authenticated users
        if user:
            market_input.user_id = user.id
            market_input.idea_id = request.idea_id
        
        # Run market sizing analysis
        report = await simple_market_sizing_workflow.run_analysis(market_input)
        execution_time = time.time() - start_time
        
        # Handle authenticated user data saving
        analysis_id = None
        message = "Market sizing analysis completed successfully"
        
        if user_email and user:
            try:
                idea_id = request.idea_id
                if not idea_id:
                    # Auto-create business idea if not provided
                    temp_idea = await user_management_service.create_business_idea(
                        user_email,
                        current_stage="idea",
                        main_goal="Market analysis",
                        biggest_challenge="Market sizing",
                        additional_info=f"Generated for: {request.business_idea}"
                    )
                    idea_id = temp_idea.id
                    message = "Market sizing analysis completed and saved to your account (new idea created)!"
                else:
                    # Verify idea belongs to user
                    await user_management_service.get_business_idea(user_email, idea_id)
                    message = "Market sizing analysis completed and saved to your account!"
                
                # Save analysis results (replace previous market sizing for same idea)
                saved_analysis = await analysis_storage_service.save_analysis_result(
                    user_id=user.id,
                    idea_id=idea_id,
                    analysis_type=AnalysisType.MARKET_SIZING,
                    market_sizing_report=report,
                    execution_time=execution_time
                )
                
                analysis_id = saved_analysis.id
                
            except Exception as save_error:
                print(f"Failed to save market sizing analysis for user {user_email}: {save_error}")
                message = "Market sizing analysis completed successfully (saving failed)"
        
        return MarketSizingResponse(
            status="completed",
            report=report,
            analysis_id=analysis_id,
            message=message,
            execution_time=execution_time
        )
        
    except Exception as e:
        print(f"Market sizing analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Market sizing analysis failed: {str(e)}"
        )


@router.get("/analyze/{idea_id}", response_model=MarketSizingResponse)
async def get_saved_market_sizing(
    idea_id: str,
    authorization: str = Depends(security)
):
    """
    Get saved market sizing analysis for an idea
    """
    try:
        # Authenticate user
        user_email = await auth_service.get_current_user_email(authorization.credentials)
        user = await auth_service.get_user_by_email(user_email)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authenticated"
            )
        
        # Get saved analysis
        saved_analysis = await analysis_storage_service.get_user_analysis(
            user.id, idea_id, AnalysisType.MARKET_SIZING, include_feedback=True
        )
        
        if not saved_analysis or not saved_analysis.market_sizing_report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Market sizing analysis not found for this idea"
            )
        
        # Get user's feedback for this analysis
        user_feedback = await feedback_service.get_user_feedback(user.id, saved_analysis.id)
        
        return MarketSizingResponse(
            status="completed",
            report=saved_analysis.market_sizing_report,
            analysis_id=saved_analysis.id,
            message="Market sizing analysis retrieved successfully",
            execution_time=saved_analysis.execution_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error retrieving saved market sizing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve market sizing analysis: {str(e)}"
        )


@router.get("/history", response_model=MarketSizingHistory)
async def get_market_sizing_history(
    page: int = 1,
    per_page: int = 10,
    authorization: str = Depends(security)
):
    """
    Get user's market sizing analysis history
    """
    try:
        # Authenticate user
        user_email = await auth_service.get_current_user_email(authorization.credentials)
        user = await auth_service.get_user_by_email(user_email)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authenticated"
            )
        
        # Get user's market sizing history
        history = await analysis_storage_service.get_user_analyses_history(
            user.id, AnalysisType.MARKET_SIZING, page, per_page
        )
        
        # Transform to response format
        history_items = []
        for analysis in history.analyses:
            if analysis.market_sizing_report:
                history_items.append({
                    "analysis_id": analysis.id,
                    "business_idea": analysis.market_sizing_report.market_overview.industry_overview[:100] + "...",
                    "industry": "Market Analysis",  # Generic since we don't store this separately
                    "tam": analysis.market_sizing_report.tam_sam_som.tam,
                    "sam": analysis.market_sizing_report.tam_sam_som.sam,
                    "som": analysis.market_sizing_report.tam_sam_som.som,
                    "confidence_level": analysis.market_sizing_report.confidence_level,
                    "created_at": analysis.created_at,
                    "has_feedback": analysis.has_feedback
                })
        
        return MarketSizingHistory(
            total_count=history.total_count,
            analyses=history_items,
            page=page,
            per_page=per_page,
            total_pages=history.total_pages
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error retrieving market sizing history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve market sizing history: {str(e)}"
        )


@router.get("/opportunity-insights/{idea_id}", response_model=MarketOpportunityResponse)
async def get_market_opportunity_insights(
    idea_id: str,
    authorization: str = Depends(security)
):
    """
    Get market opportunity insights for a specific business idea
    """
    try:
        # Authenticate user
        user_email = await auth_service.get_current_user_email(authorization.credentials)
        user = await auth_service.get_user_by_email(user_email)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authenticated"
            )
        
        # Get saved market sizing analysis
        saved_analysis = await analysis_storage_service.get_user_analysis(
            user.id, idea_id, AnalysisType.MARKET_SIZING, include_feedback=False
        )
        
        if not saved_analysis or not saved_analysis.market_sizing_report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Market sizing analysis not found for this idea"
            )
        
        report = saved_analysis.market_sizing_report
        
        # Generate opportunity insights
        key_insights = []
        
        # TAM/SAM/SOM insights
        if report.tam_sam_som.tam > 1_000_000_000:  # $1B+
            key_insights.append({
                "title": "Large Market Opportunity",
                "description": f"Total addressable market of ${report.tam_sam_som.tam:,.0f}",
                "value": report.tam_sam_som.tam,
                "confidence": report.confidence_level
            })
        
        # Growth insights
        if report.market_overview.projected_growth_rate > 10:
            key_insights.append({
                "title": "High Growth Market",
                "description": f"Projected growth rate of {report.market_overview.projected_growth_rate}% annually",
                "value": report.market_overview.projected_growth_rate,
                "confidence": report.confidence_level
            })
        
        # Market penetration insights
        if report.tam_sam_som.market_penetration_rate > 5:
            key_insights.append({
                "title": "Achievable Market Penetration",
                "description": f"Realistic market penetration rate of {report.tam_sam_som.market_penetration_rate:.1f}%",
                "value": report.tam_sam_som.market_penetration_rate,
                "confidence": report.confidence_level
            })
        
        # Revenue projection insights
        if report.revenue_projections:
            year_5_revenue = report.revenue_projections[-1].total_revenue if len(report.revenue_projections) >= 5 else 0
            if year_5_revenue > 10_000_000:  # $10M+
                key_insights.append({
                    "title": "Strong Revenue Potential",
                    "description": f"5-year revenue projection of ${year_5_revenue:,.0f}",
                    "value": year_5_revenue,
                    "confidence": report.confidence_level
                })
        
        # Generate recommendation
        recommendation = "Promising market opportunity with significant potential."
        if report.tam_sam_som.tam > 5_000_000_000:  # $5B+
            recommendation = "Exceptional market opportunity with massive scale potential."
        elif report.tam_sam_som.tam > 1_000_000_000:  # $1B+
            recommendation = "Strong market opportunity with substantial growth potential."
        
        return MarketOpportunityResponse(
            total_market_value=report.tam_sam_som.tam,
            growth_potential=report.market_overview.projected_growth_rate,
            key_insights=key_insights,
            recommendation=recommendation,
            next_steps=report.recommendations[:3]  # Top 3 recommendations
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating market opportunity insights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate market opportunity insights: {str(e)}"
        )


@router.get("/options", response_model=MarketSizingOptions)
async def get_market_sizing_options():
    """
    Get available options for market sizing analysis
    """
    try:
        return MarketSizingOptions(
            geographic_scopes={
                "regions": {
                    "global": "Global Market",
                    "north_america": "North America",
                    "usa": "United States",
                    "canada": "Canada",
                    "europe": "Europe",
                    "asia_pacific": "Asia Pacific",
                    "latin_america": "Latin America",
                    "middle_east_africa": "Middle East & Africa",
                    "custom": "Custom Regions"
                },
                "popular_combinations": [
                    ["usa", "canada"],
                    ["usa", "europe"],
                    ["north_america", "europe"],
                    ["global"]
                ]
            },
            customer_types={
                "b2b": "Business-to-Business: Selling to other businesses",
                "b2c": "Business-to-Consumer: Selling directly to consumers",
                "b2b2c": "Business-to-Business-to-Consumer: Selling through business partners to consumers",
                "mixed": "Mixed Model: Combination of B2B and B2C approaches"
            },
            revenue_models={
                "subscription": "Recurring subscription fees (SaaS, memberships)",
                "one_time_purchase": "One-time product or service sales",
                "freemium": "Free basic tier with premium paid features",
                "marketplace": "Commission or fees from marketplace transactions",
                "advertising": "Revenue from advertising and sponsorships",
                "transaction_fee": "Fees charged per transaction or usage",
                "licensing": "Licensing intellectual property or technology",
                "mixed": "Combination of multiple revenue streams"
            },
            industry_benchmarks=[
                {
                    "industry": "Software/Technology",
                    "typical_growth_rate": "15-25% annually",
                    "market_concentration": "High competition, winner-takes-most",
                    "average_tam_size": "$10B - $500B",
                    "key_metrics": {
                        "CAC": "Customer Acquisition Cost",
                        "LTV": "Customer Lifetime Value",
                        "ARR": "Annual Recurring Revenue"
                    }
                },
                {
                    "industry": "Healthcare",
                    "typical_growth_rate": "5-10% annually",
                    "market_concentration": "Regulated, high barriers to entry",
                    "average_tam_size": "$50B - $1T",
                    "key_metrics": {
                        "Regulatory_Approval": "FDA/CE approvals required",
                        "Reimbursement": "Insurance coverage rates",
                        "Clinical_Evidence": "Efficacy and safety data"
                    }
                },
                {
                    "industry": "E-commerce/Retail",
                    "typical_growth_rate": "8-15% annually",
                    "market_concentration": "Fragmented with major players",
                    "average_tam_size": "$20B - $2T",
                    "key_metrics": {
                        "GMV": "Gross Merchandise Value",
                        "AOV": "Average Order Value",
                        "Conversion_Rate": "Purchase conversion rates"
                    }
                }
            ],
            pricing_guidelines={
                "subscription": "Consider monthly/annual pricing, typically $10-$1000+ per user",
                "one_time_purchase": "Product price based on value delivered, $1-$100,000+",
                "freemium": "Premium features typically 10-20% of free tier value",
                "marketplace": "Commission rates typically 2-30% of transaction value",
                "advertising": "CPM, CPC, or revenue share models",
                "transaction_fee": "Fixed fee or percentage, typically 1-5% of transaction"
            }
        )
        
    except Exception as e:
        print(f"Error retrieving market sizing options: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve market sizing options: {str(e)}"
        ) 