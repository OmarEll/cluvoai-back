from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials
from typing import List, Optional

from core.feedback_models import (
    FeedbackCreate, FeedbackUpdate, FeedbackResponse, AnalysisFeedbackSummary,
    ModelPerformanceMetrics, FeedbackBulkResponse, FeedbackRating, FeedbackCategory
)
from services.auth_service import auth_service
from services.feedback_service import feedback_service
from api.auth_routes import security

router = APIRouter()


async def get_current_user_email(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Dependency to get current user's email from JWT token"""
    token_data = auth_service.verify_token(credentials.credentials)
    return token_data.email


@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def create_feedback(
    feedback_data: FeedbackCreate,
    request: Request,
    user_email: str = Depends(get_current_user_email)
):
    """
    Submit feedback (rating and comment) for an analysis result
    """
    try:
        # Get user
        user = await auth_service.get_user_by_email(user_email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Extract request metadata
        user_agent = request.headers.get("user-agent")
        session_id = request.headers.get("x-session-id")
        
        # Create feedback
        feedback = await feedback_service.create_feedback(
            user_id=user.id,
            feedback_data=feedback_data,
            user_agent=user_agent,
            session_id=session_id
        )
        
        return feedback
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating feedback: {str(e)}"
        )


@router.put("/feedback/{analysis_id}", response_model=FeedbackResponse)
async def update_feedback(
    analysis_id: str,
    feedback_update: FeedbackUpdate,
    user_email: str = Depends(get_current_user_email)
):
    """
    Update existing feedback for an analysis
    """
    try:
        # Get user
        user = await auth_service.get_user_by_email(user_email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update feedback
        feedback = await feedback_service.update_feedback(
            user_id=user.id,
            analysis_id=analysis_id,
            feedback_update=feedback_update
        )
        
        return feedback
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating feedback: {str(e)}"
        )


@router.get("/feedback/{analysis_id}", response_model=Optional[FeedbackResponse])
async def get_user_feedback(
    analysis_id: str,
    user_email: str = Depends(get_current_user_email)
):
    """
    Get current user's feedback for a specific analysis
    """
    try:
        # Get user
        user = await auth_service.get_user_by_email(user_email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get feedback
        feedback = await feedback_service.get_user_feedback(user.id, analysis_id)
        return feedback
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching feedback: {str(e)}"
        )


@router.delete("/feedback/{analysis_id}")
async def delete_feedback(
    analysis_id: str,
    user_email: str = Depends(get_current_user_email)
):
    """
    Delete user's feedback for an analysis
    """
    try:
        # Get user
        user = await auth_service.get_user_by_email(user_email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Delete feedback
        success = await feedback_service.delete_feedback(user.id, analysis_id)
        
        if success:
            return {"message": "Feedback deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feedback not found"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting feedback: {str(e)}"
        )


@router.get("/feedback/analysis/{analysis_id}/summary", response_model=AnalysisFeedbackSummary)
async def get_analysis_feedback_summary(
    analysis_id: str,
    user_email: Optional[str] = Depends(lambda: None)  # Optional auth
):
    """
    Get feedback summary for an analysis (includes user's feedback if authenticated)
    """
    try:
        user_id = None
        if user_email:
            user = await auth_service.get_user_by_email(user_email)
            if user:
                user_id = user.id
        
        summary = await feedback_service.get_analysis_feedback_summary(analysis_id, user_id)
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching feedback summary: {str(e)}"
        )


@router.get("/feedback/my-history", response_model=FeedbackBulkResponse)
async def get_my_feedback_history(
    limit: int = 50,
    offset: int = 0,
    user_email: str = Depends(get_current_user_email)
):
    """
    Get current user's feedback history with pagination
    """
    try:
        # Get user
        user = await auth_service.get_user_by_email(user_email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get feedback history
        history = await feedback_service.get_user_feedback_history(
            user.id, limit, offset
        )
        
        return history
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching feedback history: {str(e)}"
        )


@router.get("/analytics/performance/{analysis_type}", response_model=ModelPerformanceMetrics)
async def get_model_performance(
    analysis_type: str,
    days: int = 30,
    user_email: str = Depends(get_current_user_email)
):
    """
    Get performance metrics for an analysis type (admin/analytics endpoint)
    """
    try:
        # Verify analysis type
        if analysis_type not in ["competitor", "persona"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid analysis type. Must be 'competitor' or 'persona'"
            )
        
        # Get metrics
        metrics = await feedback_service.get_model_performance_metrics(analysis_type, days)
        return metrics
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching performance metrics: {str(e)}"
        )


@router.get("/feedback/quick-rate/{analysis_id}")
async def quick_rate_analysis(
    analysis_id: str,
    rating: FeedbackRating,
    user_email: str = Depends(get_current_user_email)
):
    """
    Quick rating endpoint for simple like/dislike without detailed feedback
    """
    try:
        # Get user
        user = await auth_service.get_user_by_email(user_email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Create simple feedback
        feedback_data = FeedbackCreate(
            analysis_id=analysis_id,
            rating=rating
        )
        
        feedback = await feedback_service.create_feedback(
            user_id=user.id,
            feedback_data=feedback_data
        )
        
        return {
            "message": f"Analysis {rating.value}d successfully",
            "rating": rating.value,
            "analysis_id": analysis_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error rating analysis: {str(e)}"
        )


@router.get("/feedback/options")
async def get_feedback_options():
    """
    Get available feedback options (ratings, categories, score ranges)
    """
    return {
        "ratings": [rating.value for rating in FeedbackRating],
        "categories": [category.value for category in FeedbackCategory],
        "score_range": {
            "min": 1,
            "max": 5,
            "description": "1 = Poor, 2 = Fair, 3 = Good, 4 = Very Good, 5 = Excellent"
        },
        "comment_max_length": 1000
    }


@router.get("/health")
async def feedback_health_check():
    """
    Health check for feedback service
    """
    return {
        "status": "healthy",
        "service": "feedback_management",
        "features": [
            "Analysis result rating (like/dislike)",
            "Detailed feedback with comments",
            "Category-specific feedback",
            "Score-based ratings (1-5)",
            "Feedback history and analytics",
            "Model performance tracking"
        ]
    } 