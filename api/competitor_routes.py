from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
import asyncio
import uuid
import time
from datetime import datetime

from api.schemas import CompetitorAnalysisRequest, CompetitorAnalysisResponse
from core.competitor_models import BusinessInput, CompetitorReport
from core.analysis_models import AnalysisType
from core.user_models import BusinessIdea, BusinessIdeaCreate, CurrentStage
from workflows.competitor_analysis_workflow import CompetitorAnalysisWorkflow
from services.auth_service import auth_service
from services.user_management_service import user_management_service
from services.analysis_storage_service import analysis_storage_service

router = APIRouter()
security = HTTPBearer(auto_error=False)

# In-memory storage for async results (use Redis/DB in production)
analysis_results: Dict[str, Dict[str, Any]] = {}


async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[str]:
    """Optional authentication - returns user email if authenticated, None if not"""
    if not credentials:
        return None
    
    try:
        token_data = auth_service.verify_token(credentials.credentials)
        return token_data.email
    except:
        return None


@router.post("/analyze/competitors", response_model=CompetitorAnalysisResponse)
async def analyze_competitors(
    request: CompetitorAnalysisRequest,
    user_email: str = Depends(get_current_user_optional)
):
    """
    Start competitor analysis for a business idea.
    Requires authentication and idea_id. Extracts all needed information from the idea.
    """
    try:
        if not user_email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        start_time = time.time()
        
        # Get the business idea to extract all needed information
        business_idea = await user_management_service.get_business_idea(user_email, request.idea_id)
        if not business_idea:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business idea not found"
            )
        
        # Create business input from the idea data
        business_input = BusinessInput(
            idea_description=business_idea.description,
            target_market=business_idea.target_who or business_idea.target_market or "General market",
            business_model=None,  # Will be inferred from description
            geographic_focus=business_idea.geographic_focus.value if business_idea.geographic_focus else "international",
            industry=business_idea.industry or "Technology"
        )
        
        # Initialize workflow
        workflow = CompetitorAnalysisWorkflow()
        
        # Run analysis
        report = await workflow.run_analysis(business_input)
        execution_time = time.time() - start_time
        
        # Get user and save the results
        user = await auth_service.get_user_by_email(user_email)
        if user:
            # Save analysis results
            await analysis_storage_service.save_analysis_result(
                user_id=user.id,
                idea_id=request.idea_id,
                analysis_type=AnalysisType.COMPETITOR,
                competitor_report=report,
                execution_time=execution_time
            )
            
            message = "Competitor analysis completed and saved to your account!"
        else:
            message = "Competitor analysis completed successfully"
        
        # Return results with analysis_id if saved
        response_data = {
            "status": "completed",
            "report": report,
            "message": message
        }
        
        # Include analysis_id if user is authenticated and results were saved
        if user_email and user:
            try:
                # Get the most recent analysis for this idea to get the analysis_id
                recent_analysis = await analysis_storage_service.get_user_analysis(
                    user.id, idea_id if 'idea_id' in locals() else None, AnalysisType.COMPETITOR, include_feedback=False
                )
                if recent_analysis and recent_analysis.id:
                    response_data["analysis_id"] = recent_analysis.id
            except:
                pass  # Don't fail the response if we can't get the analysis_id
        
        return CompetitorAnalysisResponse(**response_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Analysis failed: {str(e)}"
        )


@router.post("/analyze/competitors/async")
async def analyze_competitors_async(
    request: CompetitorAnalysisRequest, 
    background_tasks: BackgroundTasks,
    user_email: str = Depends(get_current_user_optional)
):
    """
    Start async competitor analysis (for long-running analyses)
    """
    try:
        if not user_email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Verify the idea belongs to the user
        business_idea = await user_management_service.get_business_idea(user_email, request.idea_id)
        if not business_idea:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business idea not found"
            )
        
        # Generate unique analysis ID
        analysis_id = str(uuid.uuid4())
        
        # Store initial status
        analysis_results[analysis_id] = {
            "status": "processing",
            "started_at": datetime.utcnow().isoformat(),
            "progress": 0,
            "report": None,
            "error": None,
            "user_email": user_email,
            "idea_id": request.idea_id
        }
        
        # Add background task
        background_tasks.add_task(
            run_async_analysis, 
            analysis_id, 
            request,
            user_email
        )
        
        return JSONResponse(
            status_code=202,
            content={
                "analysis_id": analysis_id,
                "status": "processing",
                "message": "Analysis started. Use GET /analyze/competitors/{analysis_id} to check status."
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start analysis: {str(e)}"
        )


@router.get("/analyze/competitors/{analysis_id}")
async def get_analysis_status(analysis_id: str):
    """
    Get status of async competitor analysis
    """
    if analysis_id not in analysis_results:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found"
        )
    
    result = analysis_results[analysis_id]
    
    if result["status"] == "completed":
        return CompetitorAnalysisResponse(
            status="completed",
            report=result["report"],
            message="Analysis completed successfully"
        )
    elif result["status"] == "failed":
        return JSONResponse(
            status_code=500,
            content={
                "status": "failed",
                "error": result["error"],
                "message": "Analysis failed"
            }
        )
    else:
        return JSONResponse(
            content={
                "status": result["status"],
                "progress": result["progress"],
                "started_at": result["started_at"],
                "message": "Analysis in progress"
            }
        )


@router.get("/analyze/last-analysis/{idea_id}")
async def get_last_competitor_analysis(
    idea_id: str,
    user_email: str = Depends(get_current_user_optional)
):
    """
    Get the last competitor analysis for a specific business idea
    """
    try:
        if not user_email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Get user
        user = await auth_service.get_user_by_email(user_email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Simple search in saved_analyses collection for the given idea_id
        from core.database import get_saved_analyses_collection
        
        # Direct query based on test results
        analysis_doc = await get_saved_analyses_collection().find_one(
            {
                "idea_id": idea_id,
                "analysis_type": "competitor"
            },
            sort=[("created_at", -1)]  # Get the most recent
        )
        
        if not analysis_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No competitor analysis found for this idea"
            )
        
        return {
            "status": "found",
            "analysis_id": analysis_doc.get("id"),
            "report": analysis_doc.get("competitor_report"),
            "created_at": analysis_doc.get("created_at"),
            "execution_time": analysis_doc.get("execution_time"),
            "message": "Last competitor analysis retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving last analysis: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


async def run_async_analysis(analysis_id: str, request: CompetitorAnalysisRequest, user_email: str):
    """
    Background task to run competitor analysis
    """
    try:
        # Update progress
        analysis_results[analysis_id]["progress"] = 10
        
        # Get the business idea to extract all needed information
        business_idea = await user_management_service.get_business_idea(user_email, request.idea_id)
        
        # Create business input from the idea data
        business_input = BusinessInput(
            idea_description=business_idea.description,
            target_market=business_idea.target_who or business_idea.target_market or "General market",
            business_model=None,  # Will be inferred from description
            geographic_focus=business_idea.geographic_focus.value if business_idea.geographic_focus else "international",
            industry=business_idea.industry or "Technology"
        )
        
        # Update progress
        analysis_results[analysis_id]["progress"] = 25
        
        # Initialize and run workflow
        workflow = CompetitorAnalysisWorkflow()
        
        # Update progress
        analysis_results[analysis_id]["progress"] = 50
        
        # Run analysis
        report = await workflow.run_analysis(business_input)
        
        # Update progress
        analysis_results[analysis_id]["progress"] = 100
        
        # Store results
        analysis_results[analysis_id].update({
            "status": "completed",
            "report": report,
            "completed_at": datetime.utcnow().isoformat()
        })
        
        # Save results to database if user is authenticated
        try:
            user = await auth_service.get_user_by_email(user_email)
            if user:
                await analysis_storage_service.save_analysis_result(
                    user_id=user.id,
                    idea_id=request.idea_id,
                    analysis_type=AnalysisType.COMPETITOR,
                    competitor_report=report,
                    execution_time=time.time() - time.time()  # Approximate
                )
        except Exception as save_error:
            print(f"Failed to save analysis results: {save_error}")
        
    except Exception as e:
        # Store error
        analysis_results[analysis_id].update({
            "status": "failed",
            "error": str(e),
            "failed_at": datetime.utcnow().isoformat()
        })