from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid
from fastapi import HTTPException, status

from core.analysis_models import AnalysisType, SavedAnalysis, AnalysisStatus, AnalysisHistory, UserAnalyticsSummary
from core.competitor_models import CompetitorReport
from core.persona_models import PersonaReport
from core.market_models import MarketSizingReport
from core.business_model_models import BusinessModelReport
from core.business_model_canvas_models import BusinessModelCanvas
from core.database import get_saved_analyses_collection
from services.feedback_service import feedback_service


class AnalysisStorageService:
    def __init__(self):
        self.analyses_collection = get_saved_analyses_collection
    
    async def save_analysis_result(
        self, 
        user_id: str, 
        idea_id: str, 
        analysis_type: AnalysisType,
        competitor_report: Optional[CompetitorReport] = None,
        persona_report: Optional[PersonaReport] = None,
        market_sizing_report: Optional[MarketSizingReport] = None,
        business_model_report: Optional[BusinessModelReport] = None,
        business_model_canvas_report: Optional[BusinessModelCanvas] = None,
        execution_time: Optional[float] = None
    ) -> SavedAnalysis:
        """Save analysis result and replace any previous analysis of the same type for the same idea"""
        try:
            # First, delete any existing analysis of the same type for this idea
            await self.analyses_collection().delete_many({
                "user_id": user_id,
                "idea_id": idea_id,
                "analysis_type": analysis_type.value
            })
            
            # Create new analysis record
            analysis_id = str(uuid.uuid4())
            
            saved_analysis = SavedAnalysis(
                id=analysis_id,
                user_id=user_id,
                idea_id=idea_id,
                analysis_type=analysis_type,
                status=AnalysisStatus.COMPLETED,
                competitor_report=competitor_report,
                persona_report=persona_report,
                market_sizing_report=market_sizing_report,
                business_model_report=business_model_report,
                business_model_canvas_report=business_model_canvas_report,
                created_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                execution_time=execution_time
            )
            
            # Insert into database
            await self.analyses_collection().insert_one(saved_analysis.dict())
            
            # Mark analysis as completed in business idea
            try:
                from services.feature_orchestration_service import feature_orchestration_service
                await feature_orchestration_service.mark_analysis_completed(
                    user_id, idea_id, analysis_type
                )
            except Exception as e:
                print(f"Warning: Failed to mark analysis as completed in business idea: {e}")
            
            return saved_analysis
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error saving analysis result: {str(e)}"
            )
    
    async def get_user_analysis(
        self, 
        user_id: str, 
        idea_id: str, 
        analysis_type: AnalysisType,
        include_feedback: bool = True
    ) -> Optional[SavedAnalysis]:
        """Get the latest analysis of a specific type for a user's idea"""
        try:
            analysis_doc = await self.analyses_collection().find_one(
                {
                    "user_id": user_id,
                    "idea_id": idea_id,
                    "analysis_type": analysis_type.value
                },
                sort=[("created_at", -1)]  # Get the most recent
            )
            
            if analysis_doc:
                analysis = SavedAnalysis(**analysis_doc)
                
                # Include feedback summary if requested
                if include_feedback and analysis.id:
                    try:
                        feedback_summary = await feedback_service.get_analysis_feedback_summary(
                            analysis.id, user_id
                        )
                        analysis.has_feedback = feedback_summary.total_feedback > 0
                        analysis.like_count = feedback_summary.likes
                        analysis.dislike_count = feedback_summary.dislikes
                        analysis.comment_count = feedback_summary.total_comments
                        analysis.avg_accuracy_score = feedback_summary.avg_accuracy
                        analysis.avg_usefulness_score = feedback_summary.avg_usefulness
                        analysis.feedback_summary = {
                            "total_feedback": feedback_summary.total_feedback,
                            "like_percentage": feedback_summary.like_percentage,
                            "category_breakdown": feedback_summary.category_breakdown
                        }
                    except Exception as e:
                        # Don't fail the whole request if feedback fetch fails
                        print(f"Failed to fetch feedback summary for analysis {analysis.id}: {e}")
                
                return analysis
            return None
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching analysis: {str(e)}"
            )
    
    async def get_idea_analyses(self, user_id: str, idea_id: str) -> List[SavedAnalysis]:
        """Get all analyses for a specific idea"""
        try:
            cursor = self.analyses_collection().find(
                {"user_id": user_id, "idea_id": idea_id},
                sort=[("created_at", -1)]
            )
            
            analyses = []
            async for doc in cursor:
                analyses.append(SavedAnalysis(**doc))
            
            return analyses
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching idea analyses: {str(e)}"
            )
    
    async def get_user_analyses_history(
        self, 
        user_id: str, 
        analysis_type: Optional[AnalysisType] = None,
        page: int = 1,
        per_page: int = 10
    ) -> Dict[str, Any]:
        """Get analyses history for a user with pagination and optional filtering"""
        try:
            # Build query
            query = {"user_id": user_id}
            if analysis_type:
                query["analysis_type"] = analysis_type.value
            
            # Get total count
            total_count = await self.analyses_collection().count_documents(query)
            
            # Calculate pagination
            skip = (page - 1) * per_page
            total_pages = (total_count + per_page - 1) // per_page
            
            # Get paginated results
            cursor = self.analyses_collection().find(
                query,
                sort=[("created_at", -1)],
                skip=skip,
                limit=per_page
            )
            
            analyses = []
            async for doc in cursor:
                analyses.append(SavedAnalysis(**doc))
            
            # Return simple dictionary structure that can be adapted by different endpoints
            return {
                "analyses": analyses,
                "total_count": total_count,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching user analyses: {str(e)}"
            )
    
    async def get_analysis_history_by_idea(self, user_id: str, idea_id: str) -> AnalysisHistory:
        """Get analysis history for a specific idea"""
        try:
            analyses = await self.get_idea_analyses(user_id, idea_id)
            
            return AnalysisHistory(
                user_id=user_id,
                idea_id=idea_id,
                analyses=analyses,
                total_analyses=len(analyses),
                last_analysis_date=analyses[0].created_at if analyses else None
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching analysis history: {str(e)}"
            )
    
    async def get_analysis_by_id(self, analysis_id: str) -> Optional[SavedAnalysis]:
        """Get analysis by its ID"""
        try:
            analysis_doc = await self.analyses_collection().find_one({"id": analysis_id})
            
            if analysis_doc:
                return SavedAnalysis(**analysis_doc)
            return None
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving analysis: {str(e)}"
            )

    async def get_user_analytics_summary(self, user_id: str, join_date: datetime) -> UserAnalyticsSummary:
        """Get analytics summary for a user"""
        try:
            # Get all analyses for the user
            analyses = await self.get_user_analyses_history(user_id)
            
            # Calculate analytics
            total_analyses = len(analyses)
            competitor_analyses = [a for a in analyses if a.analysis_type == AnalysisType.COMPETITOR]
            persona_analyses = [a for a in analyses if a.analysis_type == AnalysisType.PERSONA]
            
            # Calculate average execution time
            execution_times = [a.execution_time for a in analyses if a.execution_time is not None]
            avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else None
            
            # Find most active idea (idea with most analyses)
            idea_counts = {}
            for analysis in analyses:
                idea_counts[analysis.idea_id] = idea_counts.get(analysis.idea_id, 0) + 1
            
            most_active_idea = max(idea_counts.items(), key=lambda x: x[1])[0] if idea_counts else None
            
            # Get last activity date
            last_activity = analyses[0].created_at if analyses else None
            
            # Count unique ideas (this would need to be fetched from user data)
            unique_ideas = len(set(a.idea_id for a in analyses))
            
            return UserAnalyticsSummary(
                user_id=user_id,
                total_ideas=unique_ideas,
                total_analyses=total_analyses,
                competitor_analyses_count=len(competitor_analyses),
                persona_analyses_count=len(persona_analyses),
                avg_execution_time=avg_execution_time,
                most_active_idea=most_active_idea,
                join_date=join_date,
                last_activity=last_activity
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating analytics summary: {str(e)}"
            )
    
    async def delete_idea_analyses(self, user_id: str, idea_id: str) -> int:
        """Delete all analyses for a specific idea"""
        try:
            result = await self.analyses_collection().delete_many({
                "user_id": user_id,
                "idea_id": idea_id
            })
            
            return result.deleted_count
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting idea analyses: {str(e)}"
            )
    
    async def create_pending_analysis(
        self, 
        user_id: str, 
        idea_id: str, 
        analysis_type: AnalysisType
    ) -> SavedAnalysis:
        """Create a pending analysis record for tracking"""
        try:
            analysis_id = str(uuid.uuid4())
            
            pending_analysis = SavedAnalysis(
                id=analysis_id,
                user_id=user_id,
                idea_id=idea_id,
                analysis_type=analysis_type,
                status=AnalysisStatus.PENDING,
                created_at=datetime.utcnow()
            )
            
            # Insert into database
            await self.analyses_collection().insert_one(pending_analysis.dict())
            
            return pending_analysis
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating pending analysis: {str(e)}"
            )
    
    async def update_analysis_status(
        self, 
        analysis_id: str, 
        status: AnalysisStatus, 
        error_message: Optional[str] = None
    ) -> bool:
        """Update analysis status"""
        try:
            update_data = {"status": status.value}
            
            if status == AnalysisStatus.PROCESSING:
                update_data["processing_started_at"] = datetime.utcnow()
            elif status == AnalysisStatus.FAILED and error_message:
                update_data["error_message"] = error_message
                update_data["completed_at"] = datetime.utcnow()
            
            result = await self.analyses_collection().update_one(
                {"id": analysis_id},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating analysis status: {str(e)}"
            )


# Create global instance
analysis_storage_service = AnalysisStorageService() 