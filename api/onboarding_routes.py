from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Dict

from core.user_models import (
    OnboardingRequest, OnboardingResponse, OnboardingQuestionnaire,
    BusinessLevel, CurrentStage, MainGoal, BiggestChallenge
)
from services.auth_service import auth_service
from services.user_management_service import user_management_service
from services.analysis_storage_service import analysis_storage_service
from core.analysis_models import AnalysisType
from api.auth_routes import security

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


async def get_current_user_email(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Dependency to get current user's email from JWT token"""
    token_data = auth_service.verify_token(credentials.credentials)
    return token_data.email

@router.post("/questionnaire", response_model=OnboardingResponse)
async def submit_onboarding_questionnaire(
    request: OnboardingRequest,
    user_email: str = Depends(get_current_user_email)
):
    """
    Process onboarding questionnaire and create personalized business idea
    """
    try:
        questionnaire = request.questionnaire
        
        # Process the questionnaire and create business idea
        business_idea = await user_management_service.process_onboarding_questionnaire(
            user_email, questionnaire
        )
        
        # Generate personalized recommendations
        next_steps, feature_roadmap = user_management_service.generate_personalized_recommendations(
            questionnaire
        )
        
        return OnboardingResponse(
            message=f"Welcome! We've created your business idea and personalized your journey based on your {questionnaire.current_stage.value} stage.",
            business_idea=business_idea,
            recommended_next_steps=next_steps,
            feature_roadmap=feature_roadmap
        )
        
    except Exception as e:
        print(f"Error in onboarding questionnaire: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process onboarding questionnaire: {str(e)}"
        )

@router.get("/options")
async def get_onboarding_options():
    """
    Get all available options for the onboarding questionnaire
    """
    return {
        "business_levels": [
            {"value": level.value, "label": _get_business_level_label(level)} 
            for level in BusinessLevel
        ],
        "current_stages": [
            {"value": stage.value, "label": _get_current_stage_label(stage)} 
            for stage in CurrentStage
        ],
        "main_goals": [
            {"value": goal.value, "label": _get_main_goal_label(goal)} 
            for goal in MainGoal
        ],
        "biggest_challenges": [
            {"value": challenge.value, "label": _get_biggest_challenge_label(challenge)} 
            for challenge in BiggestChallenge
        ],
        "business_idea_format": {
            "description": "Please describe your business idea in this format:",
            "template": "We help [WHO] solve [WHAT problem] by [HOW]",
            "example": "We help small business owners solve inventory management problems by providing an AI-powered tracking platform"
        }
    }

@router.get("/personalized-roadmap/{idea_id}")
async def get_personalized_roadmap(
    idea_id: str,
    user_email: str = Depends(get_current_user_email)
):
    """
    Get personalized feature roadmap based on completed analyses
    """
    try:
        
        # Get business idea
        business_idea = await user_management_service.get_business_idea(user_email, idea_id)
        if not business_idea:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business idea not found"
            )
        
        # Check which analyses are completed
        completed_analyses = await _get_completed_analyses(user_email, idea_id)
        
        # Generate intelligent next steps based on completion status
        next_steps = await _generate_intelligent_next_steps(
            business_idea, completed_analyses
        )
        
        # Get contextual insights from completed analyses
        contextual_insights = await _get_contextual_insights(
            user_email, idea_id, completed_analyses
        )
        
        return {
            "business_idea": business_idea,
            "completed_analyses": completed_analyses,
            "recommended_next_steps": next_steps,
            "contextual_insights": contextual_insights,
            "available_features": [
                {
                    "feature": "competitor_analysis",
                    "status": "completed" if "competitor" in completed_analyses else "available",
                    "benefit": "Understand market competition and identify gaps"
                },
                {
                    "feature": "persona_analysis", 
                    "status": "completed" if "persona" in completed_analyses else "available",
                    "benefit": "Deep dive into your target customer needs"
                },
                {
                    "feature": "market_sizing",
                    "status": "completed" if "market_sizing" in completed_analyses else "available", 
                    "benefit": "Quantify your market opportunity and revenue potential"
                }
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting personalized roadmap: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get personalized roadmap: {str(e)}"
        )

# Helper functions

def _get_business_level_label(level: BusinessLevel) -> str:
    labels = {
        BusinessLevel.FIRST_TIME: "First time entrepreneur with an idea",
        BusinessLevel.SOME_EXPERIENCE: "Have some business experience (5-10 years)",
        BusinessLevel.EXPERIENCED: "Experienced entrepreneur/founder"
    }
    return labels.get(level, level.value)

def _get_current_stage_label(stage: CurrentStage) -> str:
    labels = {
        CurrentStage.IDEA: "Have an idea, haven't validated it yet",
        CurrentStage.VALIDATING: "Validating idea with potential customers",
        CurrentStage.BUILDING: "Building/developing my product",
        CurrentStage.LAUNCHING: "Ready to launch or already launched"
    }
    return labels.get(stage, stage.value)

def _get_main_goal_label(goal: MainGoal) -> str:
    labels = {
        MainGoal.VALIDATE_IDEA: "Validate if people want my idea",
        MainGoal.FIND_CUSTOMERS: "Find and talk to potential customers",
        MainGoal.BUILD_MVP: "Build my first version/MVP",
        MainGoal.GET_PAYING_CUSTOMERS: "Get my first paying customers"
    }
    return labels.get(goal, goal.value)

def _get_biggest_challenge_label(challenge: BiggestChallenge) -> str:
    labels = {
        BiggestChallenge.NEED_VALIDATION: "Don't know if anyone actually needs this",
        BiggestChallenge.FIND_CUSTOMERS: "Don't know how to find customers to talk to",
        BiggestChallenge.WHAT_TO_BUILD: "Don't know what to build first",
        BiggestChallenge.GET_SALES: "Don't know how to get people to buy",
        BiggestChallenge.OVERWHELMED: "Feel overwhelmed and don't know where to start"
    }
    return labels.get(challenge, challenge.value)

async def _get_completed_analyses(user_email: str, idea_id: str) -> List[str]:
    """Check which analyses have been completed for this idea"""
    completed = []
    
    try:
        # Check competitor analysis
        competitor_analysis = await analysis_storage_service.get_user_analysis(
            user_email, idea_id, AnalysisType.COMPETITOR, include_feedback=False
        )
        if competitor_analysis:
            completed.append("competitor")
        
        # Check persona analysis
        persona_analysis = await analysis_storage_service.get_user_analysis(
            user_email, idea_id, AnalysisType.PERSONA, include_feedback=False
        )
        if persona_analysis:
            completed.append("persona")
        
        # Check market sizing analysis
        market_sizing_analysis = await analysis_storage_service.get_user_analysis(
            user_email, idea_id, AnalysisType.MARKET_SIZING, include_feedback=False
        )
        if market_sizing_analysis:
            completed.append("market_sizing")
            
    except Exception as e:
        print(f"Error checking completed analyses: {e}")
    
    return completed

async def _generate_intelligent_next_steps(
    business_idea: dict, 
    completed_analyses: List[str]
) -> List[str]:
    """Generate intelligent next steps based on what's already completed"""
    next_steps = []
    
    # If no analyses completed yet
    if not completed_analyses:
        if business_idea.get("biggest_challenge") == BiggestChallenge.NEED_VALIDATION.value:
            next_steps.append("Start with persona analysis to validate customer needs")
        elif business_idea.get("biggest_challenge") == BiggestChallenge.WHAT_TO_BUILD.value:
            next_steps.append("Begin with competitor analysis to see what exists and find gaps")
        else:
            next_steps.append("Start with competitor analysis to understand your market landscape")
        return next_steps
    
    # If competitor analysis is done but others aren't
    if "competitor" in completed_analyses:
        if "persona" not in completed_analyses:
            next_steps.append("Run persona analysis to understand your target customers better")
            next_steps.append("Use competitor insights to identify underserved customer segments")
        if "market_sizing" not in completed_analyses:
            next_steps.append("Conduct market sizing analysis using competitor pricing intelligence")
    
    # If persona analysis is done but others aren't
    if "persona" in completed_analyses:
        if "competitor" not in completed_analyses:
            next_steps.append("Analyze competitors to see how they serve your target personas")
        if "market_sizing" not in completed_analyses:
            next_steps.append("Size your market using persona insights for accurate targeting")
    
    # If both competitor and persona are done
    if "competitor" in completed_analyses and "persona" in completed_analyses:
        if "market_sizing" not in completed_analyses:
            next_steps.append("Run market sizing with rich context from competitor and persona analyses")
            next_steps.append("Leverage competitive pricing and customer insights for accurate calculations")
        else:
            next_steps.append("All core analyses complete! Review insights for strategic planning")
            next_steps.append("Consider developing your go-to-market strategy")
    
    # If market sizing is done but others aren't
    if "market_sizing" in completed_analyses:
        if "competitor" not in completed_analyses:
            next_steps.append("Add competitor analysis to validate market sizing assumptions")
        if "persona" not in completed_analyses:
            next_steps.append("Run persona analysis to better target your market segments")
    
    return next_steps[:4]  # Limit to 4 next steps

async def _get_contextual_insights(
    user_email: str, 
    idea_id: str, 
    completed_analyses: List[str]
) -> Dict[str, str]:
    """Get key insights from completed analyses"""
    insights = {}
    
    try:
        if "competitor" in completed_analyses:
            competitor_analysis = await analysis_storage_service.get_user_analysis(
                user_email, idea_id, AnalysisType.COMPETITOR, include_feedback=False
            )
            if competitor_analysis and competitor_analysis.competitor_report:
                insights["competitor"] = f"Found {competitor_analysis.competitor_report.total_competitors} competitors with {len(competitor_analysis.competitor_report.market_gaps)} market gaps identified"
        
        if "persona" in completed_analyses:
            persona_analysis = await analysis_storage_service.get_user_analysis(
                user_email, idea_id, AnalysisType.PERSONA, include_feedback=False
            )
            if persona_analysis and persona_analysis.persona_report:
                insights["persona"] = f"Identified {len(persona_analysis.persona_report.personas)} target personas with detailed behavioral insights"
        
        if "market_sizing" in completed_analyses:
            market_analysis = await analysis_storage_service.get_user_analysis(
                user_email, idea_id, AnalysisType.MARKET_SIZING, include_feedback=False
            )
            if market_analysis and market_analysis.market_sizing_report:
                tam = market_analysis.market_sizing_report.tam_sam_som_breakdown.tam
                insights["market_sizing"] = f"Total addressable market estimated at ${tam:,.0f} with detailed revenue projections"
                
    except Exception as e:
        print(f"Error getting contextual insights: {e}")
    
    return insights 