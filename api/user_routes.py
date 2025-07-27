from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials
from typing import List

from core.user_models import (
    UserUpdate, UserResponse, BusinessIdea, BusinessIdeaCreate, 
    BusinessIdeaUpdate, CurrentStage, ExperienceLevel
)
from core.analysis_models import AnalysisHistory, UserAnalyticsSummary
from services.auth_service import auth_service
from services.user_management_service import user_management_service
from services.analysis_storage_service import analysis_storage_service
from api.auth_routes import security

router = APIRouter()


async def get_current_user_email(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Dependency to get current user's email from JWT token"""
    token_data = auth_service.verify_token(credentials.credentials)
    return token_data.email


@router.get("/profile", response_model=UserResponse)
async def get_user_profile(user_email: str = Depends(get_current_user_email)):
    """
    Get current user's profile including all business ideas
    """
    try:
        user = await auth_service.get_user_by_email(user_email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get user's ideas
        ideas = await user_management_service.get_user_ideas(user_email)
        
        return UserResponse(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            birthday=getattr(user, 'birthday', None),
            experience_level=getattr(user, 'experience_level', None),
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login,
            ideas=ideas
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching profile: {str(e)}"
        )


@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    user_email: str = Depends(get_current_user_email)
):
    """
    Update user profile information
    """
    return await user_management_service.update_user_profile(user_email, user_update)


@router.post("/ideas", response_model=BusinessIdea, status_code=status.HTTP_201_CREATED)
async def create_business_idea(
    idea_data: BusinessIdeaCreate,
    user_email: str = Depends(get_current_user_email)
):
    """
    Create a new business idea
    """
    return await user_management_service.create_business_idea(user_email, idea_data)


@router.get("/ideas", response_model=List[BusinessIdea])
async def get_user_ideas(user_email: str = Depends(get_current_user_email)):
    """
    Get all business ideas for the current user
    """
    return await user_management_service.get_user_ideas(user_email)


@router.get("/ideas/{idea_id}", response_model=BusinessIdea)
async def get_business_idea(
    idea_id: str,
    user_email: str = Depends(get_current_user_email)
):
    """
    Get a specific business idea
    """
    return await user_management_service.get_business_idea(user_email, idea_id)


@router.put("/ideas/{idea_id}", response_model=BusinessIdea)
async def update_business_idea(
    idea_id: str,
    idea_update: BusinessIdeaUpdate,
    user_email: str = Depends(get_current_user_email)
):
    """
    Update a business idea
    """
    return await user_management_service.update_business_idea(user_email, idea_id, idea_update)


@router.delete("/ideas/{idea_id}")
async def delete_business_idea(
    idea_id: str,
    user_email: str = Depends(get_current_user_email)
):
    """
    Delete a business idea and all its associated analyses
    """
    try:
        # Get user to get user_id
        user = await auth_service.get_user_by_email(user_email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Delete associated analyses first
        deleted_analyses = await analysis_storage_service.delete_idea_analyses(user.id, idea_id)
        
        # Delete the idea
        success = await user_management_service.delete_business_idea(user_email, idea_id)
        
        return {
            "message": "Business idea deleted successfully",
            "deleted_analyses": deleted_analyses
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting business idea: {str(e)}"
        )


@router.get("/ideas/{idea_id}/analyses", response_model=AnalysisHistory)
async def get_idea_analysis_history(
    idea_id: str,
    user_email: str = Depends(get_current_user_email)
):
    """
    Get analysis history for a specific business idea
    """
    try:
        # Get user to get user_id
        user = await auth_service.get_user_by_email(user_email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify idea belongs to user
        await user_management_service.get_business_idea(user_email, idea_id)
        
        # Get analysis history
        return await analysis_storage_service.get_analysis_history_by_idea(user.id, idea_id)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching analysis history: {str(e)}"
        )


@router.get("/analytics", response_model=UserAnalyticsSummary)
async def get_user_analytics(user_email: str = Depends(get_current_user_email)):
    """
    Get analytics summary for the current user
    """
    try:
        user = await auth_service.get_user_by_email(user_email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return await analysis_storage_service.get_user_analytics_summary(
            user.id, 
            user.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching analytics: {str(e)}"
        )


@router.get("/stages", response_model=List[str])
async def get_business_stages():
    """
    Get all available business development stages
    """
    return [stage.value for stage in CurrentStage]


@router.get("/experience-levels", response_model=List[str])
async def get_experience_levels():
    """
    Get all available experience levels
    """
    return [level.value for level in ExperienceLevel]


@router.get("/health")
async def user_management_health():
    """
    Health check for user management service
    """
    return {
        "status": "healthy",
        "service": "user_management",
        "features": [
            "User profile management",
            "Business idea CRUD operations",
            "Analysis history tracking",
            "User analytics and insights"
        ]
    } 