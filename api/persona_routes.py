from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
import asyncio
import uuid
import time
from datetime import datetime

from api.persona_schemas import PersonaAnalysisRequest, PersonaAnalysisResponse
from core.persona_models import PersonaAnalysisInput, PersonaReport
from core.analysis_models import AnalysisType
from core.user_models import BusinessIdea, BusinessIdeaCreate, CurrentStage
from workflows.persona_analysis_workflow import PersonaAnalysisWorkflow
from services.auth_service import auth_service
from services.user_management_service import user_management_service
from services.analysis_storage_service import analysis_storage_service

router = APIRouter()
security = HTTPBearer(auto_error=False)

# In-memory storage for async results (use Redis/DB in production)
persona_analysis_results: Dict[str, Dict[str, Any]] = {}


async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[str]:
    """Optional authentication - returns user email if authenticated, None if not"""
    if not credentials:
        return None
    
    try:
        token_data = auth_service.verify_token(credentials.credentials)
        return token_data.email
    except:
        return None


@router.post("/analyze/personas", response_model=PersonaAnalysisResponse)
async def analyze_personas(
    request: PersonaAnalysisRequest,
    user_email: str = Depends(get_current_user_optional)
):
    """
    Analyze target personas for a business idea using social media insights.
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
        
        # Create analysis input from the business idea data
        analysis_input = PersonaAnalysisInput(
            business_idea=business_idea.description,
            target_market=business_idea.target_who or business_idea.target_market or "General market",
            industry=business_idea.industry or "Technology",
            geographic_focus=business_idea.geographic_focus.value if business_idea.geographic_focus else "international",
            product_category="Mobile App"  # Default category
        )
        
        # Initialize workflow
        workflow = PersonaAnalysisWorkflow()
        
        # Run analysis
        report = await workflow.run_analysis(analysis_input)
        execution_time = time.time() - start_time
        
        # Get user and save the results
        user = await auth_service.get_user_by_email(user_email)
        if user:
            try:
                # Save analysis results
                await analysis_storage_service.save_analysis_result(
                    user_id=user.id,
                    idea_id=request.idea_id,
                    analysis_type=AnalysisType.PERSONA,
                    persona_report=report,
                    execution_time=execution_time
                )
                message = "Persona analysis completed and saved to your account!"
            except Exception as save_error:
                print(f"Failed to save analysis for user {user_email}: {save_error}")
                message = "Persona analysis completed successfully (saving failed)"
        else:
            message = "Persona analysis completed successfully"
        
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
                    user.id, request.idea_id, AnalysisType.PERSONA, include_feedback=False
                )
                if recent_analysis and recent_analysis.id:
                    response_data["analysis_id"] = recent_analysis.id
            except:
                pass  # Don't fail the response if we can't get the analysis_id
        
        return PersonaAnalysisResponse(**response_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Persona analysis failed: {str(e)}"
        )


@router.post("/analyze/personas/async")
async def analyze_personas_async(
    request: PersonaAnalysisRequest, 
    background_tasks: BackgroundTasks,
    user_email: str = Depends(get_current_user_optional)
):
    """
    Start async persona analysis (for long-running analyses)
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
        persona_analysis_results[analysis_id] = {
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
            run_async_persona_analysis, 
            analysis_id, 
            request,
            user_email
        )
        
        return JSONResponse(
            status_code=202,
            content={
                "analysis_id": analysis_id,
                "status": "processing",
                "message": "Persona analysis started. Use GET /analyze/personas/{analysis_id} to check status."
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start persona analysis: {str(e)}"
        )


@router.get("/analyze/personas/{analysis_id}")
async def get_persona_analysis_status(analysis_id: str):
    """
    Get status of async persona analysis
    """
    if analysis_id not in persona_analysis_results:
        raise HTTPException(
            status_code=404,
            detail="Persona analysis not found"
        )
    
    result = persona_analysis_results[analysis_id]
    
    if result["status"] == "completed":
        return PersonaAnalysisResponse(
            status="completed",
            report=result["report"],
            message="Persona analysis completed successfully"
        )
    elif result["status"] == "failed":
        return JSONResponse(
            status_code=500,
            content={
                "status": "failed",
                "error": result["error"],
                "message": "Persona analysis failed"
            }
        )
    else:
        return JSONResponse(
            content={
                "status": result["status"],
                "progress": result["progress"],
                "started_at": result["started_at"],
                "message": "Persona analysis in progress"
            }
        )


@router.get("/personas/example")
async def get_example_personas():
    """
    Get example personas for demo purposes
    """
    from services.persona_analysis.persona_generator_service import PersonaGeneratorService
    from core.persona_models import PersonaAnalysisInput
    
    generator = PersonaGeneratorService()
    
    # Create example input
    example_input = PersonaAnalysisInput(
        business_idea="AI-powered HR recruitment tool for small businesses",
        target_market="Small to medium businesses",
        industry="Human Resources Technology"
    )
    
    # Generate example personas
    example_personas = generator._generate_fallback_personas(example_input)
    
    return {
        "example_personas": example_personas,
        "total_personas": len(example_personas),
        "message": "Example personas for HR recruitment tool"
    }


async def run_async_persona_analysis(analysis_id: str, request: PersonaAnalysisRequest, user_email: str):
    """
    Background task to run persona analysis
    """
    try:
        # Update progress
        persona_analysis_results[analysis_id]["progress"] = 10
        
        # Get the business idea to extract all needed information
        business_idea = await user_management_service.get_business_idea(user_email, request.idea_id)
        
        # Create analysis input from the business idea data
        analysis_input = PersonaAnalysisInput(
            business_idea=business_idea.description,
            target_market=business_idea.target_who or business_idea.target_market or "General market",
            industry=business_idea.industry or "Technology",
            geographic_focus=business_idea.geographic_focus.value if business_idea.geographic_focus else "international",
            product_category="Mobile App"  # Default category
        )
        
        # Update progress
        persona_analysis_results[analysis_id]["progress"] = 25
        
        # Initialize and run workflow
        workflow = PersonaAnalysisWorkflow()
        
        # Update progress
        persona_analysis_results[analysis_id]["progress"] = 50
        
        # Run analysis
        report = await workflow.run_analysis(analysis_input)
        
        # Update progress
        persona_analysis_results[analysis_id]["progress"] = 100
        
        # Get user and save the results
        user = await auth_service.get_user_by_email(user_email)
        if user:
            try:
                await analysis_storage_service.save_analysis_result(
                    user_id=user.id,
                    idea_id=request.idea_id,
                    analysis_type=AnalysisType.PERSONA,
                    persona_report=report,
                    execution_time=0.0  # Will be calculated
                )
            except Exception as save_error:
                print(f"Failed to save async analysis for user {user_email}: {save_error}")
        
        # Store results
        persona_analysis_results[analysis_id].update({
            "status": "completed",
            "report": report,
            "completed_at": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        # Store error
        persona_analysis_results[analysis_id].update({
            "status": "failed",
            "error": str(e),
            "failed_at": datetime.utcnow().isoformat()
        })


@router.get("/analyze/last-persona-analysis/{idea_id}")
async def get_last_persona_analysis(idea_id: str, user_email: str = Depends(get_current_user_optional)):
    """
    Get the last persona analysis performed for a specific idea_id.
    This is just a search in saved_analyses table with the field idea_id, do not generate a new persona analysis.
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
        
        # Get the most recent persona analysis for this idea
        from core.database import get_saved_analyses_collection
        
        analysis_doc = await get_saved_analyses_collection().find_one(
            {
                "idea_id": idea_id,
                "analysis_type": "persona"
            },
            sort=[("created_at", -1)]  # Get the most recent
        )
        
        if not analysis_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No persona analysis found for this idea"
            )
        
        return {
            "analysis_id": analysis_doc.get("id"),
            "idea_id": idea_id,
            "analysis_type": "persona",
            "status": analysis_doc.get("status", "completed"),
            "report": analysis_doc.get("persona_report"),
            "created_at": analysis_doc.get("created_at"),
            "completed_at": analysis_doc.get("completed_at"),
            "execution_time": analysis_doc.get("execution_time"),
            "message": "Last persona analysis retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error retrieving last persona analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve last persona analysis: {str(e)}"
        )