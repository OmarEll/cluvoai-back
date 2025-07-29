from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List

from core.user_models import (
    BusinessIdea, BusinessIdeaCreate, BusinessIdeaUpdate
)
from services.user_management_service import user_management_service
from services.auth_service import auth_service
from api.auth_routes import security

router = APIRouter(prefix="/users", tags=["users"])


async def get_current_user_email(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Dependency to get current user's email from JWT token"""
    token_data = auth_service.verify_token(credentials.credentials)
    return token_data.email


@router.get("/ideas", response_model=List[BusinessIdea])
async def get_user_ideas(user_email: str = Depends(get_current_user_email)):
    """
    Get all business ideas for the current user
    """
    try:
        ideas = await user_management_service.get_user_ideas(user_email)
        return ideas
        
    except Exception as e:
        print(f"Error fetching user ideas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching ideas: {str(e)}"
        )


@router.post("/ideas", response_model=BusinessIdea, status_code=status.HTTP_201_CREATED)
async def create_business_idea(
    idea_data: BusinessIdeaCreate,
    user_email: str = Depends(get_current_user_email)
):
    """
    Create a new business idea for the current user
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
    Update a business idea
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
    Delete a business idea
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


@router.get("/health")
async def health_check():
    """Health check endpoint for user service"""
    return {"status": "healthy", "service": "user_management"} 