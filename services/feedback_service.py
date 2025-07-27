from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import uuid
from fastapi import HTTPException, status
from pymongo.errors import DuplicateKeyError

from core.feedback_models import (
    UserFeedback, FeedbackCreate, FeedbackUpdate, FeedbackResponse,
    AnalysisFeedbackSummary, ModelPerformanceMetrics, FeedbackAnalytics,
    FeedbackRating, FeedbackCategory, FeedbackBulkResponse
)
from core.analysis_models import AnalysisType
from core.database import get_feedback_collection, get_saved_analyses_collection


class FeedbackService:
    def __init__(self):
        self.feedback_collection = get_feedback_collection
        self.analyses_collection = get_saved_analyses_collection
    
    async def create_feedback(
        self, 
        user_id: str, 
        feedback_data: FeedbackCreate,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> FeedbackResponse:
        """Create or update user feedback for an analysis"""
        try:
            # Verify the analysis exists and belongs to the user
            analysis = await self.analyses_collection().find_one({
                "id": feedback_data.analysis_id,
                "user_id": user_id
            })
            
            if not analysis:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Analysis not found or you don't have permission to rate it"
                )
            
            feedback_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            # Create feedback document
            feedback_doc = UserFeedback(
                id=feedback_id,
                user_id=user_id,
                analysis_id=feedback_data.analysis_id,
                analysis_type=analysis["analysis_type"],
                rating=feedback_data.rating,
                category=feedback_data.category,
                comment=feedback_data.comment,
                accuracy_score=feedback_data.accuracy_score,
                usefulness_score=feedback_data.usefulness_score,
                created_at=now,
                user_agent=user_agent,
                session_id=session_id
            )
            
            # Use upsert to replace existing feedback from same user for same analysis
            await self.feedback_collection().replace_one(
                {
                    "user_id": user_id,
                    "analysis_id": feedback_data.analysis_id
                },
                feedback_doc.dict(),
                upsert=True
            )
            
            # Update analysis feedback summary
            await self._update_analysis_feedback_summary(feedback_data.analysis_id)
            
            return FeedbackResponse(
                id=feedback_id,
                analysis_id=feedback_data.analysis_id,
                rating=feedback_data.rating,
                category=feedback_data.category,
                comment=feedback_data.comment,
                accuracy_score=feedback_data.accuracy_score,
                usefulness_score=feedback_data.usefulness_score,
                created_at=now,
                can_edit=True
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating feedback: {str(e)}"
            )
    
    async def update_feedback(
        self, 
        user_id: str, 
        analysis_id: str, 
        feedback_update: FeedbackUpdate
    ) -> FeedbackResponse:
        """Update existing user feedback"""
        try:
            # Find existing feedback
            existing_feedback = await self.feedback_collection().find_one({
                "user_id": user_id,
                "analysis_id": analysis_id
            })
            
            if not existing_feedback:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Feedback not found"
                )
            
            # Build update document
            update_data = {"updated_at": datetime.utcnow()}
            
            if feedback_update.rating is not None:
                update_data["rating"] = feedback_update.rating
            if feedback_update.category is not None:
                update_data["category"] = feedback_update.category
            if feedback_update.comment is not None:
                update_data["comment"] = feedback_update.comment
            if feedback_update.accuracy_score is not None:
                update_data["accuracy_score"] = feedback_update.accuracy_score
            if feedback_update.usefulness_score is not None:
                update_data["usefulness_score"] = feedback_update.usefulness_score
            
            # Update feedback
            await self.feedback_collection().update_one(
                {"user_id": user_id, "analysis_id": analysis_id},
                {"$set": update_data}
            )
            
            # Update analysis feedback summary
            await self._update_analysis_feedback_summary(analysis_id)
            
            # Get updated feedback
            updated_feedback = await self.feedback_collection().find_one({
                "user_id": user_id,
                "analysis_id": analysis_id
            })
            
            return FeedbackResponse(
                id=updated_feedback["id"],
                analysis_id=updated_feedback["analysis_id"],
                rating=updated_feedback["rating"],
                category=updated_feedback["category"],
                comment=updated_feedback.get("comment"),
                accuracy_score=updated_feedback.get("accuracy_score"),
                usefulness_score=updated_feedback.get("usefulness_score"),
                created_at=updated_feedback["created_at"],
                updated_at=updated_feedback.get("updated_at"),
                can_edit=True
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating feedback: {str(e)}"
            )
    
    async def get_user_feedback(self, user_id: str, analysis_id: str) -> Optional[FeedbackResponse]:
        """Get user's feedback for a specific analysis"""
        try:
            feedback = await self.feedback_collection().find_one({
                "user_id": user_id,
                "analysis_id": analysis_id
            })
            
            if not feedback:
                return None
            
            return FeedbackResponse(
                id=feedback["id"],
                analysis_id=feedback["analysis_id"],
                rating=feedback["rating"],
                category=feedback["category"],
                comment=feedback.get("comment"),
                accuracy_score=feedback.get("accuracy_score"),
                usefulness_score=feedback.get("usefulness_score"),
                created_at=feedback["created_at"],
                updated_at=feedback.get("updated_at"),
                can_edit=True
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching user feedback: {str(e)}"
            )
    
    async def get_analysis_feedback_summary(self, analysis_id: str, user_id: Optional[str] = None) -> AnalysisFeedbackSummary:
        """Get feedback summary for an analysis"""
        try:
            # Get all feedback for this analysis
            cursor = self.feedback_collection().find({"analysis_id": analysis_id})
            feedback_list = await cursor.to_list(length=None)
            
            if not feedback_list:
                return AnalysisFeedbackSummary(
                    analysis_id=analysis_id,
                    analysis_type="unknown"
                )
            
            # Calculate metrics
            total_feedback = len(feedback_list)
            likes = sum(1 for f in feedback_list if f["rating"] == FeedbackRating.LIKE)
            dislikes = total_feedback - likes
            like_percentage = (likes / total_feedback * 100) if total_feedback > 0 else 0
            
            # Calculate average scores
            accuracy_scores = [f.get("accuracy_score") for f in feedback_list if f.get("accuracy_score")]
            usefulness_scores = [f.get("usefulness_score") for f in feedback_list if f.get("usefulness_score")]
            
            avg_accuracy = sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else None
            avg_usefulness = sum(usefulness_scores) / len(usefulness_scores) if usefulness_scores else None
            
            # Category breakdown
            category_breakdown = {}
            for feedback in feedback_list:
                category = feedback.get("category", "overall")
                category_breakdown[category] = category_breakdown.get(category, 0) + 1
            
            # Comments
            comments = [f for f in feedback_list if f.get("comment")]
            
            # Get user's feedback if authenticated
            user_feedback = None
            if user_id:
                user_feedback = await self.get_user_feedback(user_id, analysis_id)
            
            return AnalysisFeedbackSummary(
                analysis_id=analysis_id,
                analysis_type=feedback_list[0]["analysis_type"],
                total_feedback=total_feedback,
                likes=likes,
                dislikes=dislikes,
                like_percentage=round(like_percentage, 1),
                avg_accuracy=round(avg_accuracy, 2) if avg_accuracy else None,
                avg_usefulness=round(avg_usefulness, 2) if avg_usefulness else None,
                category_breakdown=category_breakdown,
                has_comments=len(comments) > 0,
                total_comments=len(comments),
                user_feedback=user_feedback
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching feedback summary: {str(e)}"
            )
    
    async def delete_feedback(self, user_id: str, analysis_id: str) -> bool:
        """Delete user's feedback for an analysis"""
        try:
            result = await self.feedback_collection().delete_one({
                "user_id": user_id,
                "analysis_id": analysis_id
            })
            
            if result.deleted_count > 0:
                # Update analysis feedback summary
                await self._update_analysis_feedback_summary(analysis_id)
                return True
            
            return False
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting feedback: {str(e)}"
            )
    
    async def get_user_feedback_history(
        self, 
        user_id: str, 
        limit: int = 50, 
        offset: int = 0
    ) -> FeedbackBulkResponse:
        """Get user's feedback history"""
        try:
            # Get total count
            total_count = await self.feedback_collection().count_documents({"user_id": user_id})
            
            # Get feedback with pagination
            cursor = self.feedback_collection().find(
                {"user_id": user_id},
                sort=[("created_at", -1)],
                skip=offset,
                limit=limit
            )
            
            feedback_list = []
            async for feedback in cursor:
                feedback_list.append(FeedbackResponse(
                    id=feedback["id"],
                    analysis_id=feedback["analysis_id"],
                    rating=feedback["rating"],
                    category=feedback["category"],
                    comment=feedback.get("comment"),
                    accuracy_score=feedback.get("accuracy_score"),
                    usefulness_score=feedback.get("usefulness_score"),
                    created_at=feedback["created_at"],
                    updated_at=feedback.get("updated_at"),
                    can_edit=True
                ))
            
            has_more = (offset + len(feedback_list)) < total_count
            next_cursor = str(offset + limit) if has_more else None
            
            return FeedbackBulkResponse(
                feedback_list=feedback_list,
                total_count=total_count,
                has_more=has_more,
                next_cursor=next_cursor
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching feedback history: {str(e)}"
            )
    
    async def get_model_performance_metrics(
        self, 
        analysis_type: str, 
        days: int = 30
    ) -> ModelPerformanceMetrics:
        """Get performance metrics for a specific analysis type"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get analyses in time period
            analyses_cursor = self.analyses_collection().find({
                "analysis_type": analysis_type,
                "created_at": {"$gte": start_date}
            })
            analyses = await analyses_cursor.to_list(length=None)
            total_analyses = len(analyses)
            
            # Get feedback in time period
            feedback_cursor = self.feedback_collection().find({
                "analysis_type": analysis_type,
                "created_at": {"$gte": start_date}
            })
            feedback_list = await feedback_cursor.to_list(length=None)
            total_feedback = len(feedback_list)
            
            if total_feedback == 0:
                return ModelPerformanceMetrics(
                    analysis_type=analysis_type,
                    time_period=f"Last {days} days",
                    total_analyses=total_analyses
                )
            
            # Calculate metrics
            feedback_rate = (total_feedback / total_analyses * 100) if total_analyses > 0 else 0
            likes = sum(1 for f in feedback_list if f["rating"] == FeedbackRating.LIKE)
            overall_like_rate = (likes / total_feedback * 100) if total_feedback > 0 else 0
            
            # Calculate average scores
            accuracy_scores = [f.get("accuracy_score") for f in feedback_list if f.get("accuracy_score")]
            usefulness_scores = [f.get("usefulness_score") for f in feedback_list if f.get("usefulness_score")]
            
            avg_accuracy = sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else None
            avg_usefulness = sum(usefulness_scores) / len(usefulness_scores) if usefulness_scores else None
            
            # Category-specific like rates
            categories = [FeedbackCategory.ACCURACY, FeedbackCategory.COMPLETENESS, 
                         FeedbackCategory.RELEVANCE, FeedbackCategory.USEFULNESS]
            category_rates = {}
            
            for category in categories:
                category_feedback = [f for f in feedback_list if f.get("category") == category]
                if category_feedback:
                    category_likes = sum(1 for f in category_feedback if f["rating"] == FeedbackRating.LIKE)
                    category_rates[category] = (category_likes / len(category_feedback) * 100)
                else:
                    category_rates[category] = 0.0
            
            return ModelPerformanceMetrics(
                analysis_type=analysis_type,
                time_period=f"Last {days} days",
                total_analyses=total_analyses,
                total_feedback=total_feedback,
                feedback_rate=round(feedback_rate, 1),
                overall_like_rate=round(overall_like_rate, 1),
                avg_accuracy_score=round(avg_accuracy, 2) if avg_accuracy else None,
                avg_usefulness_score=round(avg_usefulness, 2) if avg_usefulness else None,
                accuracy_like_rate=round(category_rates[FeedbackCategory.ACCURACY], 1),
                completeness_like_rate=round(category_rates[FeedbackCategory.COMPLETENESS], 1),
                relevance_like_rate=round(category_rates[FeedbackCategory.RELEVANCE], 1),
                usefulness_like_rate=round(category_rates[FeedbackCategory.USEFULNESS], 1)
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error calculating performance metrics: {str(e)}"
            )
    
    async def _update_analysis_feedback_summary(self, analysis_id: str):
        """Update the feedback summary in the analysis document"""
        try:
            summary = await self.get_analysis_feedback_summary(analysis_id)
            
            # Update analysis document with feedback metrics
            await self.analyses_collection().update_one(
                {"id": analysis_id},
                {
                    "$set": {
                        "has_feedback": summary.total_feedback > 0,
                        "like_count": summary.likes,
                        "dislike_count": summary.dislikes,
                        "comment_count": summary.total_comments,
                        "avg_accuracy_score": summary.avg_accuracy,
                        "avg_usefulness_score": summary.avg_usefulness,
                        "feedback_summary": {
                            "total_feedback": summary.total_feedback,
                            "like_percentage": summary.like_percentage,
                            "category_breakdown": summary.category_breakdown
                        }
                    }
                }
            )
            
        except Exception as e:
            # Log error but don't raise - this is a background update
            print(f"Failed to update analysis feedback summary for {analysis_id}: {e}")


# Create global instance
feedback_service = FeedbackService() 