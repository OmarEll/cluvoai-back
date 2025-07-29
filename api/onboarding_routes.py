from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Dict

from core.user_models import (
    OnboardingRequest, OnboardingResponse, OnboardingQuestionnaire,
    BusinessLevel, CurrentStage, MainGoal, BiggestChallenge, GeographicFocus,
    # New comprehensive enums
    BusinessExperience, BusinessStage, MainGoalNew, BiggestChallengeNew, 
    GeographicFocusNew, TargetCustomerType, TargetAgeGroup, TargetIncome,
    Industry, ProblemUrgency, CompetitorKnowledge, MonetizationModel,
    ExpectedPricing, AvailableBudget, LaunchTimeline, TimeCommitment
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
            message=f"Welcome! We've created your business idea and personalized your journey based on your {questionnaire.business_stage.value} stage.",
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
    Get all available options for the comprehensive onboarding questionnaire
    """
    return {
        # Core Questions
        "business_experience": [
            {"value": exp.value, "label": _get_business_experience_label(exp)} 
            for exp in BusinessExperience
        ],
        "business_stage": [
            {"value": stage.value, "label": _get_business_stage_label(stage)} 
            for stage in BusinessStage
        ],
        "main_goal": [
            {"value": goal.value, "label": _get_main_goal_new_label(goal)} 
            for goal in MainGoalNew
        ],
        "biggest_challenge": [
            {"value": challenge.value, "label": _get_biggest_challenge_new_label(challenge)} 
            for challenge in BiggestChallengeNew
        ],
        "geographic_focus": [
            {"value": focus.value, "label": _get_geographic_focus_new_label(focus)} 
            for focus in GeographicFocusNew
        ],
        
        # Target Audience Questions
        "target_customer_type": [
            {"value": customer.value, "label": _get_target_customer_type_label(customer)} 
            for customer in TargetCustomerType
        ],
        "target_age_group": [
            {"value": age.value, "label": _get_target_age_group_label(age)} 
            for age in TargetAgeGroup
        ],
        "target_income": [
            {"value": income.value, "label": _get_target_income_label(income)} 
            for income in TargetIncome
        ],
        
        # Market Context
        "industry": [
            {"value": ind.value, "label": _get_industry_label(ind)} 
            for ind in Industry
        ],
        "problem_urgency": [
            {"value": urgency.value, "label": _get_problem_urgency_label(urgency)} 
            for urgency in ProblemUrgency
        ],
        
        # Competitive Awareness
        "competitor_knowledge": [
            {"value": knowledge.value, "label": _get_competitor_knowledge_label(knowledge)} 
            for knowledge in CompetitorKnowledge
        ],
        
        # Business Model
        "monetization_model": [
            {"value": model.value, "label": _get_monetization_model_label(model)} 
            for model in MonetizationModel
        ],
        "expected_pricing": [
            {"value": pricing.value, "label": _get_expected_pricing_label(pricing)} 
            for pricing in ExpectedPricing
        ],
        
        # Resources & Timeline
        "available_budget": [
            {"value": budget.value, "label": _get_available_budget_label(budget)} 
            for budget in AvailableBudget
        ],
        "launch_timeline": [
            {"value": timeline.value, "label": _get_launch_timeline_label(timeline)} 
            for timeline in LaunchTimeline
        ],
        "time_commitment": [
            {"value": time.value, "label": _get_time_commitment_label(time)} 
            for time in TimeCommitment
        ],
        
        # Business Idea Format Guidance
        "business_idea_format": {
            "description": "Please describe your business idea clearly and concisely:",
            "guidelines": [
                "What problem does your idea solve?",
                "Who is your target customer?",
                "How does your solution work?",
                "What makes it unique?"
            ],
            "example": "A mobile app that helps small restaurant owners manage their inventory and reduce food waste by using AI to predict demand patterns and suggest optimal ordering quantities."
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
        # Get user's business idea
        business_idea = await user_management_service.get_business_idea(user_email, idea_id)
        if not business_idea:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business idea not found"
            )
        
        # Get completed analyses for this idea
        completed_analyses = await analysis_storage_service.get_idea_analyses(idea_id)
        
        # Generate dynamic roadmap based on current stage and completed analyses
        roadmap = user_management_service.generate_dynamic_roadmap(
            business_idea, completed_analyses
        )
        
        return {
            "idea_id": idea_id,
            "current_stage": business_idea.current_stage,
            "completed_analyses": [analysis.analysis_type for analysis in completed_analyses],
            "recommended_next_steps": roadmap["next_steps"],
            "feature_priorities": roadmap["priorities"],
            "estimated_timeline": roadmap["timeline"]
        }
        
    except Exception as e:
        print(f"Error generating personalized roadmap: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate personalized roadmap: {str(e)}"
        )

# Helper functions for label generation
def _get_business_experience_label(experience: BusinessExperience) -> str:
    labels = {
        BusinessExperience.FIRST_TIME: "First-time entrepreneur",
        BusinessExperience.STARTED_1_2: "Have started 1-2 businesses",
        BusinessExperience.SERIAL_3_PLUS: "Serial entrepreneur (3+ businesses)",
        BusinessExperience.CONSULTANT_ADVISOR: "Business consultant/advisor"
    }
    return labels.get(experience, experience.value)

def _get_business_stage_label(stage: BusinessStage) -> str:
    labels = {
        BusinessStage.JUST_IDEA: "Just an idea",
        BusinessStage.VALIDATING: "Validating the idea",
        BusinessStage.BUILDING_MVP: "Building MVP",
        BusinessStage.LAUNCHED_0_6_MONTHS: "Launched (0-6 months)",
        BusinessStage.GROWING_6_PLUS_MONTHS: "Growing (6+ months)",
        BusinessStage.SCALING_EXPANDING: "Scaling/Expanding"
    }
    return labels.get(stage, stage.value)

def _get_main_goal_new_label(goal: MainGoalNew) -> str:
    labels = {
        MainGoalNew.VALIDATE_IDEA: "Validate my idea",
        MainGoalNew.UNDERSTAND_MARKET: "Understand the market",
        MainGoalNew.FIND_CUSTOMERS: "Find customers",
        MainGoalNew.BUILD_PRODUCT: "Build the product",
        MainGoalNew.GET_FUNDING: "Get funding",
        MainGoalNew.GROW_REVENUE: "Grow revenue",
        MainGoalNew.SCALE_OPERATIONS: "Scale operations"
    }
    return labels.get(goal, goal.value)

def _get_biggest_challenge_new_label(challenge: BiggestChallengeNew) -> str:
    labels = {
        BiggestChallengeNew.IDEA_WONT_WORK: "Don't know if idea will work",
        BiggestChallengeNew.UNDERSTANDING_COMPETITION: "Understanding competition",
        BiggestChallengeNew.FINDING_CUSTOMERS: "Finding customers",
        BiggestChallengeNew.BUILDING_PRODUCT: "Building the product",
        BiggestChallengeNew.GETTING_FUNDING: "Getting funding",
        BiggestChallengeNew.MARKETING_SALES: "Marketing/Sales",
        BiggestChallengeNew.TEAM_BUILDING: "Team building",
        BiggestChallengeNew.OTHER: "Other"
    }
    return labels.get(challenge, challenge.value)

def _get_geographic_focus_new_label(focus: GeographicFocusNew) -> str:
    labels = {
        GeographicFocusNew.LOCAL_CITY: "Local/City",
        GeographicFocusNew.STATE_PROVINCE: "State/Province",
        GeographicFocusNew.COUNTRY_WIDE: "Country-wide",
        GeographicFocusNew.NORTH_AMERICA: "North America",
        GeographicFocusNew.EUROPE: "Europe",
        GeographicFocusNew.ASIA: "Asia",
        GeographicFocusNew.GLOBAL: "Global",
        GeographicFocusNew.OTHER: "Other"
    }
    return labels.get(focus, focus.value)

def _get_target_customer_type_label(customer: TargetCustomerType) -> str:
    labels = {
        TargetCustomerType.B2C_CONSUMERS: "Individual consumers (B2C)",
        TargetCustomerType.SMALL_BUSINESS_1_50: "Small businesses (1-50 employees)",
        TargetCustomerType.MID_MARKET_51_500: "Mid-market (51-500 employees)",
        TargetCustomerType.ENTERPRISE_500_PLUS: "Enterprise (500+ employees)",
        TargetCustomerType.GOVERNMENT_NONPROFIT: "Government/Non-profit",
        TargetCustomerType.OTHER: "Other"
    }
    return labels.get(customer, customer.value)

def _get_target_age_group_label(age: TargetAgeGroup) -> str:
    labels = {
        TargetAgeGroup.AGE_18_25: "18-25",
        TargetAgeGroup.AGE_26_35: "26-35",
        TargetAgeGroup.AGE_36_45: "36-45",
        TargetAgeGroup.AGE_46_55: "46-55",
        TargetAgeGroup.AGE_55_PLUS: "55+",
        TargetAgeGroup.ALL_AGES: "All ages"
    }
    return labels.get(age, age.value)

def _get_target_income_label(income: TargetIncome) -> str:
    labels = {
        TargetIncome.UNDER_50K: "Under $50K",
        TargetIncome.FROM_50K_100K: "$50K-$100K",
        TargetIncome.FROM_100K_250K: "$100K-$250K",
        TargetIncome.OVER_250K: "$250K+",
        TargetIncome.ENTERPRISE_BUDGET: "Enterprise budget",
        TargetIncome.NOT_RELEVANT: "Not relevant"
    }
    return labels.get(income, income.value)

def _get_industry_label(industry: Industry) -> str:
    labels = {
        Industry.TECHNOLOGY_SOFTWARE: "Technology/Software",
        Industry.HEALTHCARE: "Healthcare",
        Industry.FINANCE_FINTECH: "Finance/Fintech",
        Industry.ECOMMERCE_RETAIL: "E-commerce/Retail",
        Industry.EDUCATION: "Education",
        Industry.REAL_ESTATE: "Real Estate",
        Industry.MANUFACTURING: "Manufacturing",
        Industry.FOOD_BEVERAGE: "Food & Beverage",
        Industry.PROFESSIONAL_SERVICES: "Professional Services",
        Industry.ENTERTAINMENT_MEDIA: "Entertainment/Media",
        Industry.OTHER: "Other"
    }
    return labels.get(industry, industry.value)

def _get_problem_urgency_label(urgency: ProblemUrgency) -> str:
    labels = {
        ProblemUrgency.CRITICAL: "Critical - customers actively seeking solutions",
        ProblemUrgency.IMPORTANT: "Important - customers aware but not urgent",
        ProblemUrgency.NICE_TO_HAVE: "Nice-to-have - customers don't actively seek solutions",
        ProblemUrgency.NOT_SURE: "Not sure"
    }
    return labels.get(urgency, urgency.value)

def _get_competitor_knowledge_label(knowledge: CompetitorKnowledge) -> str:
    labels = {
        CompetitorKnowledge.KNOW_3_PLUS: "Yes, I know 3+ direct competitors",
        CompetitorKnowledge.KNOW_1_2: "Yes, I know 1-2 competitors",
        CompetitorKnowledge.SOME_IDEAS: "I have some ideas but not sure",
        CompetitorKnowledge.DONT_KNOW: "No, I don't know my competitors"
    }
    return labels.get(knowledge, knowledge.value)

def _get_monetization_model_label(model: MonetizationModel) -> str:
    labels = {
        MonetizationModel.SUBSCRIPTION_SAAS: "Subscription/SaaS",
        MonetizationModel.ONE_TIME_PURCHASE: "One-time purchase",
        MonetizationModel.FREEMIUM: "Freemium",
        MonetizationModel.MARKETPLACE_COMMISSION: "Marketplace/Commission",
        MonetizationModel.ADVERTISING: "Advertising",
        MonetizationModel.CONSULTING_SERVICES: "Consulting/Services",
        MonetizationModel.NOT_SURE: "Not sure yet"
    }
    return labels.get(model, model.value)

def _get_expected_pricing_label(pricing: ExpectedPricing) -> str:
    labels = {
        ExpectedPricing.FREE: "Free",
        ExpectedPricing.UNDER_10_MONTH: "Under $10/month",
        ExpectedPricing.FROM_10_50_MONTH: "$10-50/month",
        ExpectedPricing.FROM_50_200_MONTH: "$50-200/month",
        ExpectedPricing.OVER_200_MONTH: "$200+/month",
        ExpectedPricing.CUSTOM_PRICING: "Custom pricing",
        ExpectedPricing.NOT_APPLICABLE: "Not applicable"
    }
    return labels.get(pricing, pricing.value)

def _get_available_budget_label(budget: AvailableBudget) -> str:
    labels = {
        AvailableBudget.UNDER_5K: "Under $5K",
        AvailableBudget.FROM_5K_25K: "$5K-$25K",
        AvailableBudget.FROM_25K_100K: "$25K-$100K",
        AvailableBudget.FROM_100K_500K: "$100K-$500K",
        AvailableBudget.OVER_500K: "$500K+",
        AvailableBudget.PRE_FUNDING: "Pre-funding/Seeking investment"
    }
    return labels.get(budget, budget.value)

def _get_launch_timeline_label(timeline: LaunchTimeline) -> str:
    labels = {
        LaunchTimeline.WITHIN_3_MONTHS: "Within 3 months",
        LaunchTimeline.FROM_3_6_MONTHS: "3-6 months",
        LaunchTimeline.FROM_6_12_MONTHS: "6-12 months",
        LaunchTimeline.OVER_12_MONTHS: "12+ months",
        LaunchTimeline.ALREADY_LAUNCHED: "Already launched"
    }
    return labels.get(timeline, timeline.value)

def _get_time_commitment_label(time: TimeCommitment) -> str:
    labels = {
        TimeCommitment.FULL_TIME_40_PLUS: "Full-time (40+ hrs/week)",
        TimeCommitment.PART_TIME_20_39: "Part-time (20-39 hrs/week)",
        TimeCommitment.SIDE_PROJECT_5_19: "Side project (5-19 hrs/week)",
        TimeCommitment.VERY_LIMITED_UNDER_5: "Very limited (<5 hrs/week)"
    }
    return labels.get(time, time.value)


# Legacy helper functions for backward compatibility
def _get_business_level_label(level: BusinessLevel) -> str:
    labels = {
        BusinessLevel.FIRST_TIME: "I'm a first-time entrepreneur",
        BusinessLevel.SOME_EXPERIENCE: "I have some business experience (5-10 years)",
        BusinessLevel.EXPERIENCED: "I'm an experienced entrepreneur"
    }
    return labels.get(level, level.value)

def _get_current_stage_label(stage: CurrentStage) -> str:
    labels = {
        CurrentStage.IDEA: "I have an idea",
        CurrentStage.VALIDATING: "I'm validating my idea",
        CurrentStage.BUILDING: "I'm building my product",
        CurrentStage.LAUNCHING: "I'm ready to launch"
    }
    return labels.get(stage, stage.value)

def _get_main_goal_label(goal: MainGoal) -> str:
    labels = {
        MainGoal.VALIDATE_IDEA: "Validate if people want my idea",
        MainGoal.FIND_CUSTOMERS: "Find and talk to customers",
        MainGoal.BUILD_MVP: "Build my first version (MVP)",
        MainGoal.GET_PAYING_CUSTOMERS: "Get my first paying customers"
    }
    return labels.get(goal, goal.value)

def _get_biggest_challenge_label(challenge: BiggestChallenge) -> str:
    labels = {
        BiggestChallenge.NEED_VALIDATION: "I don't know if anyone needs this",
        BiggestChallenge.FIND_CUSTOMERS: "I don't know how to find customers",
        BiggestChallenge.WHAT_TO_BUILD: "I don't know what to build first",
        BiggestChallenge.GET_SALES: "I don't know how to get people to buy",
        BiggestChallenge.OVERWHELMED: "I feel overwhelmed and don't know where to start"
    }
    return labels.get(challenge, challenge.value)

def _get_geographic_focus_label(focus: GeographicFocus) -> str:
    labels = {
        GeographicFocus.NORTH_AMERICA: "North America",
        GeographicFocus.EUROPE: "Europe",
        GeographicFocus.ASIA: "Asia",
        GeographicFocus.AFRICA: "Africa",
        GeographicFocus.SOUTH_AMERICA: "South America",
        GeographicFocus.OCEANIA: "Oceania",
        GeographicFocus.INTERNATIONAL: "International"
    }
    return labels.get(focus, focus.value) 