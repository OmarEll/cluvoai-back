from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from fastapi.security import HTTPAuthorizationCredentials
from datetime import datetime
import time

from core.analysis_models import AnalysisRequest, AnalysisResponse, AnalysisType
from core.competitor_models import BusinessInput
from core.persona_models import PersonaAnalysisInput
from services.auth_service import auth_service
from services.user_management_service import user_management_service
from services.analysis_storage_service import analysis_storage_service
from services.feedback_service import feedback_service
from workflows.competitor_analysis_workflow import CompetitorAnalysisWorkflow
from workflows.persona_analysis_workflow import PersonaAnalysisWorkflow
from api.auth_routes import security

router = APIRouter()


async def get_current_user_email(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Dependency to get current user's email from JWT token"""
    token_data = auth_service.verify_token(credentials.credentials)
    return token_data.email


@router.post("/analyze", response_model=AnalysisResponse)
async def run_analysis_for_idea(
    request: AnalysisRequest,
    user_email: str = Depends(get_current_user_email)
):
    """
    Run analysis for a specific business idea and save results
    """
    try:
        start_time = time.time()
        
        # Get user
        user = await auth_service.get_user_by_email(user_email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get business idea
        idea = await user_management_service.get_business_idea(user_email, request.idea_id)
        
        # Prepare business input based on idea data (with optional overrides)
        if request.analysis_type == AnalysisType.COMPETITOR:
            business_input = BusinessInput(
                idea_description=request.custom_description or idea.description,
                target_market=request.custom_target_market or idea.target_market,
                business_model=None,  # Could be added to BusinessIdea model
                geographic_focus=None,  # Could be added to BusinessIdea model
                industry=request.custom_industry or idea.industry
            )
            
            # Run competitor analysis
            workflow = CompetitorAnalysisWorkflow()
            report = await workflow.run_analysis(business_input)
            
            # Save results to database (replacing any previous analysis)
            saved_analysis = await analysis_storage_service.save_analysis_result(
                user_id=user.id,
                idea_id=request.idea_id,
                analysis_type=AnalysisType.COMPETITOR,
                competitor_report=report,
                execution_time=time.time() - start_time
            )
            
            return AnalysisResponse(
                analysis_id=saved_analysis.id,
                status=saved_analysis.status,
                message="Competitor analysis completed successfully",
                competitor_report=report,
                created_at=saved_analysis.created_at,
                completed_at=saved_analysis.completed_at,
                execution_time=saved_analysis.execution_time,
                can_provide_feedback=True,
                feedback_summary=None,  # New analysis, no feedback yet
                user_feedback=None
            )
            
        elif request.analysis_type == AnalysisType.PERSONA:
            persona_input = PersonaAnalysisInput(
                business_idea=request.custom_description or idea.description,
                target_market=request.custom_target_market or idea.target_market,
                industry=request.custom_industry or idea.industry,
                geographic_focus=None,  # Could be added to BusinessIdea model
                product_category=None   # Could be added to BusinessIdea model
            )
            
            # Run persona analysis with enhanced context
            workflow = PersonaAnalysisWorkflow()
            
            # Enhance the persona input with user and idea context for competitor analysis lookup
            enhanced_state = PersonaAnalysisState(
                analysis_input=persona_input,
                user_id=user.id,
                idea_id=request.idea_id
            )
            
            # Run the enhanced workflow
            final_state = await workflow.workflow.ainvoke(enhanced_state)
            report = final_state.final_report
            
            # Save results to database (replacing any previous analysis)
            saved_analysis = await analysis_storage_service.save_analysis_result(
                user_id=user.id,
                idea_id=request.idea_id,
                analysis_type=AnalysisType.PERSONA,
                persona_report=report,
                execution_time=time.time() - start_time
            )
            
            return AnalysisResponse(
                analysis_id=saved_analysis.id,
                status=saved_analysis.status,
                message="Persona analysis completed successfully",
                persona_report=report,
                created_at=saved_analysis.created_at,
                completed_at=saved_analysis.completed_at,
                execution_time=saved_analysis.execution_time,
                can_provide_feedback=True,
                feedback_summary=None,  # New analysis, no feedback yet
                user_feedback=None
            )
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid analysis type"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get("/analyze/{idea_id}/{analysis_type}", response_model=AnalysisResponse)
async def get_saved_analysis(
    idea_id: str,
    analysis_type: AnalysisType,
    user_email: str = Depends(get_current_user_email)
):
    """
    Get the most recent saved analysis for an idea
    """
    try:
        # Get user
        user = await auth_service.get_user_by_email(user_email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify idea belongs to user
        await user_management_service.get_business_idea(user_email, idea_id)
        
        # Get saved analysis
        saved_analysis = await analysis_storage_service.get_user_analysis(
            user.id, idea_id, analysis_type
        )
        
        if not saved_analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No {analysis_type.value} analysis found for this idea"
            )
        
        # Get user's feedback for this analysis
        user_feedback = await feedback_service.get_user_feedback(user.id, saved_analysis.id)
        
        return AnalysisResponse(
            analysis_id=saved_analysis.id,
            status=saved_analysis.status,
            message=f"Retrieved saved {analysis_type.value} analysis",
            competitor_report=saved_analysis.competitor_report,
            persona_report=saved_analysis.persona_report,
            created_at=saved_analysis.created_at,
            completed_at=saved_analysis.completed_at,
            execution_time=saved_analysis.execution_time,
            can_provide_feedback=True,
            feedback_summary=saved_analysis.feedback_summary,
            user_feedback=user_feedback.dict() if user_feedback else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving analysis: {str(e)}"
        )


@router.post("/analyze/async", response_model=dict)
async def run_analysis_async(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    user_email: str = Depends(get_current_user_email)
):
    """
    Start async analysis for a business idea
    """
    try:
        # Get user
        user = await auth_service.get_user_by_email(user_email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify idea belongs to user
        await user_management_service.get_business_idea(user_email, request.idea_id)
        
        # Create pending analysis record
        pending_analysis = await analysis_storage_service.create_pending_analysis(
            user.id, request.idea_id, request.analysis_type
        )
        
        # Add background task
        background_tasks.add_task(
            run_background_analysis,
            pending_analysis.id,
            user.id,
            user_email,
            request
        )
        
        return {
            "analysis_id": pending_analysis.id,
            "status": "processing",
            "message": f"{request.analysis_type.value.title()} analysis started in background",
            "idea_id": request.idea_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting async analysis: {str(e)}"
        )


async def run_background_analysis(
    analysis_id: str,
    user_id: str, 
    user_email: str,
    request: AnalysisRequest
):
    """Background task to run analysis"""
    try:
        # Update status to processing
        await analysis_storage_service.update_analysis_status(
            analysis_id, 
            status="processing"
        )
        
        start_time = time.time()
        
        # Get business idea
        idea = await user_management_service.get_business_idea(user_email, request.idea_id)
        
        # Run analysis based on type
        if request.analysis_type == AnalysisType.COMPETITOR:
            business_input = BusinessInput(
                idea_description=request.custom_description or idea.description,
                target_market=request.custom_target_market or idea.target_market,
                industry=request.custom_industry or idea.industry
            )
            
            workflow = CompetitorAnalysisWorkflow()
            report = await workflow.run_analysis(business_input)
            
            # Save results
            await analysis_storage_service.save_analysis_result(
                user_id=user_id,
                idea_id=request.idea_id,
                analysis_type=AnalysisType.COMPETITOR,
                competitor_report=report,
                execution_time=time.time() - start_time
            )
            
        elif request.analysis_type == AnalysisType.PERSONA:
            persona_input = PersonaAnalysisInput(
                business_idea=request.custom_description or idea.description,
                target_market=request.custom_target_market or idea.target_market,
                industry=request.custom_industry or idea.industry
            )
            
            workflow = PersonaAnalysisWorkflow()
            report = await workflow.run_analysis(persona_input)
            
            # Save results
            await analysis_storage_service.save_analysis_result(
                user_id=user_id,
                idea_id=request.idea_id,
                analysis_type=AnalysisType.PERSONA,
                persona_report=report,
                execution_time=time.time() - start_time
            )
        
    except Exception as e:
        # Update status to failed
        await analysis_storage_service.update_analysis_status(
            analysis_id,
            status="failed", 
            error_message=str(e)
        )


@router.get("/health")
async def enhanced_analysis_health():
    """Health check for enhanced analysis service"""
    return {
        "status": "healthy",
        "service": "enhanced_analysis",
        "features": [
            "User-authenticated analysis",
            "Business idea integration",
            "Analysis result storage",
            "Analysis history tracking",
            "Automatic result replacement"
        ]
    } 