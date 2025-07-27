from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
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
    user_email: Optional[str] = Depends(get_current_user_optional)
):
    """
    Start competitor analysis for a business idea.
    If user is authenticated, results will be automatically saved to their account.
    """
    try:
        start_time = time.time()
        
        # Create business input from request
        business_input = BusinessInput(
            idea_description=request.idea_description,
            target_market=request.target_market,
            business_model=request.business_model,
            geographic_focus=request.geographic_focus,
            industry=request.industry
        )
        
        # Initialize workflow
        workflow = CompetitorAnalysisWorkflow()
        
        # Run analysis
        report = await workflow.run_analysis(business_input)
        execution_time = time.time() - start_time
        
        # If user is authenticated, save the results
        if user_email:
            try:
                # Get user
                user = await auth_service.get_user_by_email(user_email)
                if user:
                    idea_id = request.idea_id
                    
                    # If no idea_id provided, create a temporary idea
                    if not idea_id:
                        temp_idea = await user_management_service.create_business_idea(
                            user_email,
                            BusinessIdeaCreate(
                                title=f"Analysis from {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                                description=request.idea_description,
                                current_stage=CurrentStage.IDEA,
                                main_goal="Generated from competitor analysis",
                                biggest_challenge="To be defined",
                                target_market=request.target_market,
                                industry=request.industry
                            )
                        )
                        idea_id = temp_idea.id
                    else:
                        # Verify the idea belongs to the user
                        await user_management_service.get_business_idea(user_email, idea_id)
                    
                    # Save analysis results
                    await analysis_storage_service.save_analysis_result(
                        user_id=user.id,
                        idea_id=idea_id,
                        analysis_type=AnalysisType.COMPETITOR,
                        competitor_report=report,
                        execution_time=execution_time
                    )
                    
                    message = f"Competitor analysis completed and saved to your account{'!' if request.idea_id else ' (new idea created)!'}"
                else:
                    message = "Competitor analysis completed successfully"
            except Exception as save_error:
                print(f"Failed to save analysis for user {user_email}: {save_error}")
                message = "Competitor analysis completed successfully (saving failed)"
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
async def analyze_competitors_async(request: CompetitorAnalysisRequest, background_tasks: BackgroundTasks):
    """
    Start async competitor analysis (for long-running analyses)
    """
    try:
        # Generate unique analysis ID
        analysis_id = str(uuid.uuid4())
        
        # Store initial status
        analysis_results[analysis_id] = {
            "status": "processing",
            "started_at": datetime.utcnow().isoformat(),
            "progress": 0,
            "report": None,
            "error": None
        }
        
        # Add background task
        background_tasks.add_task(
            run_async_analysis, 
            analysis_id, 
            request
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


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


async def run_async_analysis(analysis_id: str, request: CompetitorAnalysisRequest):
    """
    Background task to run competitor analysis
    """
    try:
        # Update progress
        analysis_results[analysis_id]["progress"] = 10
        
        # Create business input
        business_input = BusinessInput(
            idea_description=request.idea_description,
            target_market=request.target_market,
            business_model=request.business_model,
            geographic_focus=request.geographic_focus,
            industry=request.industry
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
        
    except Exception as e:
        # Store error
        analysis_results[analysis_id].update({
            "status": "failed",
            "error": str(e),
            "failed_at": datetime.utcnow().isoformat()
        })