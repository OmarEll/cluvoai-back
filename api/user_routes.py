from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional

from core.user_models import (
    BusinessIdea, BusinessIdeaCreate, BusinessIdeaUpdate
)
from services.user_management_service import user_management_service
from services.auth_service import auth_service
from api.auth_routes import security

router = APIRouter(prefix="/users")


async def get_current_user_email(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Dependency to get current user's email from JWT token"""
    token_data = auth_service.verify_token(credentials.credentials)
    return token_data.email


@router.get("/ideas", response_model=List[BusinessIdea])
async def get_user_ideas(
    user_email: str = Depends(get_current_user_email),
    stage: Optional[str] = None,
    industry: Optional[str] = None,
    search: Optional[str] = None
):
    """
    Get all business ideas for the current user with optional filtering
    
    Returns a list of all business ideas belonging to the authenticated user,
    including all comprehensive fields from the enhanced questionnaire:
    - Business experience level and stage
    - Geographic focus and target market details  
    - Industry and problem urgency information
    - Monetization model and pricing strategy
    - Timeline and resource availability
    
    **Query Parameters:**
    - `stage`: Filter by current_stage (e.g., "have_an_idea", "validating_idea")
    - `industry`: Filter by industry (e.g., "technology_software", "healthcare")  
    - `search`: Search in title and description (case-insensitive)
    
    **Example Usage:**
    - `/api/v1/users/ideas` - Get all ideas
    - `/api/v1/users/ideas?stage=validating_idea` - Only validating ideas
    - `/api/v1/users/ideas?industry=technology_software` - Only tech ideas
    - `/api/v1/users/ideas?search=AI` - Search for "AI" in title/description
    """
    try:
        ideas = await user_management_service.get_user_ideas(user_email)
        
        # Apply filters if provided
        if stage:
            ideas = [idea for idea in ideas if idea.current_stage == stage]
        
        if industry:
            ideas = [idea for idea in ideas if idea.industry and idea.industry.lower() == industry.lower()]
            
        if search:
            search_lower = search.lower()
            ideas = [idea for idea in ideas if 
                    search_lower in idea.title.lower() or 
                    search_lower in idea.description.lower()]
        
        return ideas
        
    except Exception as e:
        print(f"Error fetching user ideas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching ideas: {str(e)}"
        )


@router.get("/ideas/statistics")
async def get_ideas_statistics(user_email: str = Depends(get_current_user_email)):
    """
    Get comprehensive statistics about user's business ideas
    
    Returns analytics and insights about all user ideas including:
    - Total number of ideas
    - Breakdown by stage, industry, geographic focus
    - Analysis completion rates
    - Most common challenges and goals
    - Recent activity summary
    
    **Example Response:**
    ```json
    {
        "total_ideas": 12,
        "by_stage": {
            "have_an_idea": 5,
            "validating_idea": 4,
            "building_product": 2,
            "ready_to_launch": 1
        },
        "by_industry": {
            "technology_software": 6,
            "healthcare": 3,
            "e_commerce": 2,
            "education": 1
        },
        "analysis_completion": {
            "competitor_analysis": 8,
            "persona_analysis": 6,
            "market_sizing": 4,
            "business_model": 3
        },
        "recent_activity": "Created 2 new ideas this week"
    }
    ```
    """
    try:
        ideas = await user_management_service.get_user_ideas(user_email)
        
        # Calculate statistics
        total_ideas = len(ideas)
        
        # Stage breakdown
        stage_counts = {}
        for idea in ideas:
            stage = idea.current_stage
            stage_counts[stage] = stage_counts.get(stage, 0) + 1
        
        # Industry breakdown  
        industry_counts = {}
        for idea in ideas:
            if idea.industry:
                industry = idea.industry
                industry_counts[industry] = industry_counts.get(industry, 0) + 1
        
        # Geographic focus breakdown
        geo_counts = {}
        for idea in ideas:
            if idea.geographic_focus:
                geo = idea.geographic_focus
                geo_counts[geo] = geo_counts.get(geo, 0) + 1
        
        # Analysis completion rates
        analysis_counts = {
            "competitor_analysis": 0,
            "persona_analysis": 0, 
            "market_sizing": 0,
            "business_model": 0,
            "business_model_canvas": 0,
            "customer_discovery": 0
        }
        
        for idea in ideas:
            if idea.completed_analyses:
                for analysis in idea.completed_analyses:
                    if analysis in analysis_counts:
                        analysis_counts[analysis] += 1
        
        return {
            "total_ideas": total_ideas,
            "by_stage": stage_counts,
            "by_industry": industry_counts, 
            "by_geographic_focus": geo_counts,
            "analysis_completion": analysis_counts,
            "avg_analyses_per_idea": round(sum(analysis_counts.values()) / max(total_ideas, 1), 1),
            "most_common_stage": max(stage_counts.items(), key=lambda x: x[1])[0] if stage_counts else None,
            "most_common_industry": max(industry_counts.items(), key=lambda x: x[1])[0] if industry_counts else None
        }
        
    except Exception as e:
        print(f"Error calculating ideas statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating statistics: {str(e)}"
        )


@router.post("/ideas", response_model=BusinessIdea, status_code=status.HTTP_201_CREATED)
async def create_business_idea(
    idea_data: BusinessIdeaCreate,
    user_email: str = Depends(get_current_user_email)
):
    """
    Create a new business idea for the current user
    
    Creates a basic business idea. For comprehensive business ideas with 
    all enhanced fields, use the onboarding questionnaire endpoint instead.
    """
    try:
        new_idea = await user_management_service.create_business_idea(user_email, idea_data)
        return new_idea
        
    except Exception as e:
        print(f"Error creating business idea: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating business idea: {str(e)}"
        )


@router.get("/ideas/{idea_id}", response_model=BusinessIdea)
async def get_business_idea(
    idea_id: str,
    user_email: str = Depends(get_current_user_email)
):
    """
    Get a specific business idea by ID
    
    Returns detailed information about a specific business idea including:
    - Basic info: title, description, current stage
    - Target market: who, what problem, how we solve it
    - Business context: experience level, geographic focus, industry
    - Monetization: model, pricing, timeline, budget
    - Analysis history: completed analyses and insights
    
    **Example Response:**
    ```json
    {
        "id": "uuid-here",
        "title": "AI-Powered Food Delivery",
        "description": "Platform using ML for delivery optimization...", 
        "current_stage": "validating_idea",
        "business_level": "first_time_entrepreneur",
        "geographic_focus": "north_america",
        "target_market": "busy professionals aged 25-45",
        "industry": "technology_software",
        "completed_analyses": ["competitor", "persona"]
    }
    ```
    """
    try:
        idea = await user_management_service.get_business_idea(user_email, idea_id)
        return idea
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching business idea: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching business idea: {str(e)}"
        )


@router.put("/ideas/{idea_id}", response_model=BusinessIdea)
async def update_business_idea(
    idea_id: str,
    idea_update: BusinessIdeaUpdate,
    user_email: str = Depends(get_current_user_email)
):
    """
    Update a business idea with all comprehensive questionnaire fields
    
    Supports updating all 18 fields from the comprehensive questionnaire:
    
    **Core Fields:**
    - `title`: Brief business idea title
    - `description`: Detailed business description  
    - `current_stage`: Current development stage
    - `main_goal`: Primary objective right now
    - `biggest_challenge`: Main obstacle faced
    - `target_market`: Target market description
    - `industry`: Industry vertical
    
    **Enhanced Fields:**
    - `business_level`: Experience level (first_time, serial_entrepreneur, etc.)
    - `geographic_focus`: Target region (local, north_america, europe, global, etc.)
    - `target_who`: WHO we help (target customers)
    - `problem_what`: WHAT problem we solve
    - `solution_how`: HOW we solve the problem
    
    **New Comprehensive Questionnaire Fields (All 18):**
    
    **Core Questions:**
    - `business_experience`: Experience level (first_time_entrepreneur, started_1_2_businesses, etc.)
    - `business_stage`: Business stage (just_an_idea, validating_the_idea, building_mvp, etc.)
    - `main_goal_new`: Main goal (validate_my_idea, understand_the_market, find_customers, etc.)
    - `biggest_challenge_new`: Biggest challenge (dont_know_if_idea_will_work, understanding_competition, etc.)
    - `geographic_focus_new`: Geographic focus (local_city, north_america, europe, global, etc.)
    
    **Target Audience:**
    - `target_customer_type`: Customer type (individual_consumers_b2c, small_businesses_1_50_employees, etc.)
    - `target_age_group`: Age groups (["18_25", "26_35", "36_45", "46_55", "55_plus", "all_ages"])
    - `target_income`: Income level (under_50k, 50k_100k, 100k_250k, 250k_plus, etc.)
    
    **Market Context:**
    - `industry_new`: Industry (technology_software, healthcare, finance_fintech, etc.)
    - `problem_urgency`: Urgency (critical_actively_seeking, important_aware_not_urgent, etc.)
    
    **Competitive Awareness:**
    - `competitor_knowledge`: Competitor knowledge (know_3_plus_direct_competitors, etc.)
    - `differentiation`: What makes you different (text field)
    
    **Business Model:**
    - `monetization_model`: Revenue model (subscription_saas, one_time_purchase, freemium, etc.)
    - `expected_pricing`: Price point (free, under_10_month, 10_50_month, etc.)
    
    **Resources & Timeline:**
    - `available_budget`: Budget (under_5k, 5k_25k, 25k_100k, 100k_500k, 500k_plus, etc.)
    - `launch_timeline`: Timeline (within_3_months, 3_6_months, 6_12_months, etc.)
    - `time_commitment`: Time commitment (full_time_40_plus_hours, part_time_20_39_hours, etc.)
    
    **Example Request:**
    ```json
    {
        "title": "Enhanced AI Fitness Coach Platform",
        "current_stage": "building_product",
        "business_experience": "started_1_2_businesses",
        "geographic_focus_new": "global",
        "industry_new": "technology_software",
        "target_customer_type": "individual_consumers_b2c",
        "target_age_group": ["26_35", "36_45"],
        "monetization_model": "subscription_saas",
        "expected_pricing": "10_50_month",
        "available_budget": "25k_100k",
        "launch_timeline": "3_6_months"
    }
    ```
    
    Only provide fields you want to update - all fields are optional.
    """
    try:
        updated_idea = await user_management_service.update_business_idea(
            user_email, idea_id, idea_update
        )
        return updated_idea
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating business idea: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating business idea: {str(e)}"
        )


@router.delete("/ideas/{idea_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_business_idea(
    idea_id: str,
    user_email: str = Depends(get_current_user_email)
):
    """
    Delete a business idea permanently
    
    ⚠️ **Warning**: This action cannot be undone!
    
    This will permanently delete:
    - The business idea and all its data
    - All associated analysis results (competitor, persona, market sizing, etc.)
    - All chat history related to this idea
    - All saved insights and recommendations
    
    Make sure you have backed up any important data before deletion.
    """
    try:
        await user_management_service.delete_business_idea(user_email, idea_id)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting business idea: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting business idea: {str(e)}"
        )


@router.post("/ideas/{idea_id}/clone", response_model=BusinessIdea, status_code=status.HTTP_201_CREATED)
async def clone_business_idea(
    idea_id: str,
    user_email: str = Depends(get_current_user_email),
    title_suffix: Optional[str] = " (Copy)"
):
    """
    Clone/duplicate an existing business idea with all comprehensive fields
    
    Creates a complete copy of an existing idea including:
    - All basic fields (title, description, stage, etc.)
    - All enhanced fields (business_level, geographic_focus, etc.)
    - Target market information
    - BUT NOT: analysis results or chat history (fresh start for new idea)
    
    **Parameters:**
    - `idea_id`: ID of the idea to clone
    - `title_suffix`: Text to append to cloned title (default: " (Copy)")
    
    **Use Cases:**
    - Create variations of successful ideas for different markets
    - Test different approaches to the same core concept  
    - Build upon previous ideas with modifications
    - Create backup versions before major changes
    
    **Example:**
    Original: "AI Food Delivery Platform"
    → Clone: "AI Food Delivery Platform (Copy)"
    """
    try:
        # Get the original idea
        original_idea = await user_management_service.get_business_idea(user_email, idea_id)
        
        # Create a new BusinessIdeaCreate from the original
        cloned_data = BusinessIdeaCreate(
            title=original_idea.title + title_suffix,
            description=original_idea.description,
            current_stage=original_idea.current_stage,
            main_goal=original_idea.main_goal,
            biggest_challenge=original_idea.biggest_challenge
        )
        
        # Create the cloned idea
        new_idea = await user_management_service.create_business_idea(user_email, cloned_data)
        
        # Now update it with all the enhanced fields from the original
        enhanced_update = BusinessIdeaUpdate(
            business_level=original_idea.business_level,
            geographic_focus=original_idea.geographic_focus,
            target_who=original_idea.target_who,
            problem_what=original_idea.problem_what,
            solution_how=original_idea.solution_how,
            target_market=original_idea.target_market,
            industry=original_idea.industry
        )
        
        # Apply the enhanced fields
        updated_idea = await user_management_service.update_business_idea(
            user_email, new_idea.id, enhanced_update
        )
        
        return updated_idea
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error cloning business idea: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cloning business idea: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint for user service"""
    return {"status": "healthy", "service": "user_management"} 