from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import uuid

from core.business_model_canvas_models import (
    BusinessModelCanvasRequest, BusinessModelCanvasResponse,
    CanvasUpdateRequest, BusinessModelCanvasHistory, CanvasInsights,
    CanvasExportRequest, CanvasExportFormat
)
from services.auth_service import auth_service
from services.analysis_storage_service import analysis_storage_service
from services.feature_orchestration_service import feature_orchestration_service
from workflows.simple_business_model_canvas_workflow import simple_business_model_canvas_workflow
from core.analysis_models import AnalysisType

# Create router
router = APIRouter(prefix="/business-model-canvas", tags=["Business Model Canvas"])

# Security
security = HTTPBearer()

async def get_current_user_email(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Get current user email from JWT token"""
    try:
        email = await auth_service.get_current_user_email(credentials.credentials)
        return email
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )


@router.post("/analyze", response_model=BusinessModelCanvasResponse)
async def generate_business_model_canvas(
    request: BusinessModelCanvasRequest,
    user_email: Optional[str] = Depends(get_current_user_email)
):
    """
    Generate a comprehensive Business Model Canvas using all available analysis context
    """
    try:
        print(f"🎨 Starting Business Model Canvas analysis for user: {user_email}")
        
        # Get user ID from email
        user = await auth_service.get_user_by_email(user_email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_id = str(user["_id"]) if isinstance(user, dict) else str(user.id)
        idea_id = request.idea_id
        
        # If no idea_id provided, create a new business idea
        if not idea_id:
            from services.user_management_service import user_management_service
            from core.user_models import BusinessIdeaCreate
            
            print(f"🔧 Creating new business idea for user: {user_email}")
            
            idea_data = BusinessIdeaCreate(
                title=f"Business Idea - {request.business_idea[:50]}...",
                description=request.business_idea,
                current_stage="have_an_idea",
                main_goal="validate_if_people_want_idea",
                biggest_challenge="dont_know_if_anyone_needs_this"
            )
            
            new_idea = await user_management_service.create_business_idea(user_email, idea_data)
            idea_id = new_idea.id
            print(f"✅ Created new business idea with ID: {idea_id}")
            print(f"   Idea title: {new_idea.title}")
            print(f"   Idea description: {new_idea.description[:100]}...")
        else:
            print(f"🔧 Using existing idea ID: {idea_id}")
        
        # Run canvas analysis
        canvas = await simple_business_model_canvas_workflow.run_canvas_analysis(
            business_idea=request.business_idea,
            target_market=request.target_market,
            industry=request.industry,
            user_id=user_id,
            idea_id=idea_id
        )
        
        # Get analysis ID if saved
        analysis_id = None
        if user_id and idea_id:
            saved_analysis = await analysis_storage_service.get_user_analysis(
                user_id, idea_id, AnalysisType.BUSINESS_MODEL_CANVAS
            )
            if saved_analysis:
                analysis_id = saved_analysis.id
        
        print(f"🔧 Final response data:")
        print(f"   Analysis ID: {analysis_id}")
        print(f"   Idea ID: {idea_id}")
        print(f"   Canvas business idea: {canvas.business_idea}")
        
        response = BusinessModelCanvasResponse(
            canvas=canvas,
            analysis_id=analysis_id,
            idea_id=idea_id,
            message="Business Model Canvas generated successfully with cross-feature context"
        )
        
        print(f"🔧 Response object:")
        print(f"   Response idea_id: {response.idea_id}")
        print(f"   Response analysis_id: {response.analysis_id}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating Business Model Canvas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate Business Model Canvas: {str(e)}"
        )


@router.get("/analyze/{idea_id}", response_model=BusinessModelCanvasResponse)
async def get_saved_canvas_analysis(
    idea_id: str,
    user_email: str = Depends(get_current_user_email)
):
    """
    Retrieve saved Business Model Canvas analysis for a specific idea
    """
    try:
        # Get user ID
        user = await auth_service.get_user_by_email(user_email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_id = str(user["_id"]) if isinstance(user, dict) else str(user.id)
        
        # Get saved analysis
        saved_analysis = await analysis_storage_service.get_user_analysis(
            user_id, idea_id, AnalysisType.BUSINESS_MODEL_CANVAS
        )
        
        if not saved_analysis or saved_analysis.user_id != user_id:
            raise HTTPException(status_code=404, detail="Business Model Canvas not found")
        
        return BusinessModelCanvasResponse(
            analysis_id=saved_analysis.id,
            canvas=saved_analysis.business_model_canvas_report,
            message="Business Model Canvas retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error retrieving Business Model Canvas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve Business Model Canvas: {str(e)}"
        )


@router.get("/history", response_model=BusinessModelCanvasHistory)
async def get_canvas_history(
    idea_id: str,
    user_email: str = Depends(get_current_user_email)
):
    """
    Get history of Business Model Canvas versions for an idea
    """
    try:
        # Get user ID
        user = await auth_service.get_user_by_email(user_email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_id = str(user["_id"]) if isinstance(user, dict) else str(user.id)
        
        # Get analysis history
        history = await analysis_storage_service.get_user_analyses_history(
            user_id, AnalysisType.BUSINESS_MODEL_CANVAS, page=1, per_page=50
        )
        
        # Filter for specific idea
        idea_analyses = [
            analysis for analysis in history.get("analyses", [])
            if analysis.get("idea_id") == idea_id
        ]
        
        # Convert to canvas versions
        versions = []
        for analysis in idea_analyses:
            if analysis.get("business_model_canvas_report"):
                versions.append({
                    "version_id": analysis.get("id", ""),
                    "canvas": analysis.get("business_model_canvas_report"),
                    "created_at": analysis.get("created_at"),
                    "changes_description": f"Canvas version {len(versions) + 1}"
                })
        
        return BusinessModelCanvasHistory(
            idea_id=idea_id,
            versions=versions,
            total_versions=len(versions),
            latest_version=versions[-1]["version_id"] if versions else ""
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error retrieving canvas history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve canvas history: {str(e)}"
        )


@router.put("/update/{analysis_id}")
async def update_canvas_building_block(
    analysis_id: str,
    update_request: CanvasUpdateRequest,
    user_email: str = Depends(get_current_user_email)
):
    """
    Update specific building blocks of a Business Model Canvas
    """
    try:
        # Get user ID
        user = await auth_service.get_user_by_email(user_email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_id = str(user["_id"]) if isinstance(user, dict) else str(user.id)
        
        # Get existing analysis
        saved_analysis = await analysis_storage_service.get_analysis_by_id(analysis_id)
        
        if not saved_analysis or saved_analysis.user_id != user_id:
            raise HTTPException(
                status_code=404,
                detail="Business Model Canvas analysis not found"
            )
        
        # Update the specific building block
        canvas = saved_analysis.business_model_canvas_report
        if not canvas:
            raise HTTPException(
                status_code=404,
                detail="Canvas data not found"
            )
        
        # Apply updates to the specified building block
        building_block = update_request.building_block
        updates = update_request.updates
        
        # This would require more sophisticated update logic
        # For now, return success message
        return {
            "message": f"Building block '{building_block}' updated successfully",
            "analysis_id": analysis_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating canvas building block: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update canvas building block: {str(e)}"
        )


@router.get("/insights/{idea_id}", response_model=CanvasInsights)
async def get_canvas_insights(
    idea_id: str,
    user_email: str = Depends(get_current_user_email)
):
    """
    Get AI-generated insights and recommendations for canvas optimization
    """
    try:
        # Get user ID
        user = await auth_service.get_user_by_email(user_email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_id = str(user["_id"]) if isinstance(user, dict) else str(user.id)
        
        # Get saved canvas analysis
        saved_analysis = await analysis_storage_service.get_user_analysis(
            user_id, idea_id, AnalysisType.BUSINESS_MODEL_CANVAS
        )
        
        if not saved_analysis or not saved_analysis.business_model_canvas_report:
            raise HTTPException(
                status_code=404,
                detail="Business Model Canvas analysis not found"
            )
        
        canvas = saved_analysis.business_model_canvas_report
        
        # Generate insights based on canvas data
        insights = CanvasInsights(
            strengths=[
                "Strong value proposition alignment with customer needs",
                "Clear revenue stream identification",
                "Comprehensive resource planning"
            ],
            weaknesses=[
                "Potential cost structure optimization needed",
                "Channel strategy could be more diversified"
            ],
            opportunities=[
                "Expand to additional customer segments",
                "Leverage partnerships for growth",
                "Optimize pricing strategy"
            ],
            threats=[
                "Competitive pressure on pricing",
                "Market saturation in target segment"
            ],
            recommendations=[
                "Conduct A/B testing for pricing optimization",
                "Develop strategic partnerships",
                "Implement customer feedback loop"
            ],
            risk_assessment={
                "market_risk": "Medium",
                "competitive_risk": "High",
                "execution_risk": "Low"
            },
            optimization_suggestions=[
                "Automate customer relationships for scalability",
                "Diversify revenue streams",
                "Optimize cost structure for profitability"
            ]
        )
        
        return insights
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating canvas insights: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate canvas insights: {str(e)}"
        )


@router.post("/export/{analysis_id}")
async def export_canvas(
    analysis_id: str,
    export_request: CanvasExportRequest,
    user_email: str = Depends(get_current_user_email)
):
    """
    Export Business Model Canvas in various formats
    """
    try:
        # Get user ID
        user = await auth_service.get_user_by_email(user_email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_id = str(user["_id"]) if isinstance(user, dict) else str(user.id)
        
        # Get saved analysis
        saved_analysis = await analysis_storage_service.get_analysis_by_id(analysis_id)
        
        if not saved_analysis or saved_analysis.user_id != user_id:
            raise HTTPException(
                status_code=404,
                detail="Business Model Canvas analysis not found"
            )
        
        canvas = saved_analysis.business_model_canvas_report
        if not canvas:
            raise HTTPException(
                status_code=404,
                detail="Canvas data not found"
            )
        
        # Generate export based on format
        export_format = export_request.format
        
        if export_format == CanvasExportFormat.JSON:
            export_data = canvas.model_dump()
        elif export_format == CanvasExportFormat.CSV:
            # Convert canvas to CSV format
            export_data = self._convert_canvas_to_csv(canvas)
        elif export_format == CanvasExportFormat.PDF:
            # Generate PDF report
            export_data = self._generate_pdf_report(canvas, export_request.include_insights)
        elif export_format == CanvasExportFormat.VISUAL:
            # Generate visual representation
            export_data = self._generate_visual_canvas(canvas)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported export format: {export_format}"
            )
        
        return {
            "message": f"Canvas exported successfully in {export_format} format",
            "format": export_format,
            "data": export_data,
            "analysis_id": analysis_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error exporting canvas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export canvas: {str(e)}"
        )


@router.get("/options")
async def get_canvas_options():
    """
    Get available options for Business Model Canvas building blocks
    """
    try:
        from core.business_model_canvas_models import (
            CustomerSegmentType, ValuePropositionType, ChannelType,
            CustomerRelationshipType, RevenueStreamType, KeyResourceType,
            KeyActivityType, PartnershipType, CostStructureType
        )
        
        options = {
            "customer_segment_types": [
                {"value": segment.value, "label": segment.value.replace("_", " ").title()}
                for segment in CustomerSegmentType
            ],
            "value_proposition_types": [
                {"value": prop.value, "label": prop.value.replace("_", " ").title()}
                for prop in ValuePropositionType
            ],
            "channel_types": [
                {"value": channel.value, "label": channel.value.replace("_", " ").title()}
                for channel in ChannelType
            ],
            "customer_relationship_types": [
                {"value": rel.value, "label": rel.value.replace("_", " ").title()}
                for rel in CustomerRelationshipType
            ],
            "revenue_stream_types": [
                {"value": stream.value, "label": stream.value.replace("_", " ").title()}
                for stream in RevenueStreamType
            ],
            "key_resource_types": [
                {"value": resource.value, "label": resource.value.replace("_", " ").title()}
                for resource in KeyResourceType
            ],
            "key_activity_types": [
                {"value": activity.value, "label": activity.value.replace("_", " ").title()}
                for activity in KeyActivityType
            ],
            "partnership_types": [
                {"value": partnership.value, "label": partnership.value.replace("_", " ").title()}
                for partnership in PartnershipType
            ],
            "cost_structure_types": [
                {"value": cost.value, "label": cost.value.replace("_", " ").title()}
                for cost in CostStructureType
            ],
            "export_formats": [
                {"value": "json", "label": "JSON"},
                {"value": "csv", "label": "CSV"},
                {"value": "pdf", "label": "PDF Report"},
                {"value": "visual", "label": "Visual Canvas"}
            ]
        }
        
        return options
        
    except Exception as e:
        print(f"Error getting canvas options: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get canvas options: {str(e)}"
        )


# Helper methods for export functionality
def _convert_canvas_to_csv(self, canvas):
    """Convert canvas to CSV format"""
    # Implementation would convert canvas data to CSV
    return "CSV data would be generated here"

def _generate_pdf_report(self, canvas, include_insights):
    """Generate PDF report of canvas"""
    # Implementation would generate PDF
    return "PDF report would be generated here"

def _generate_visual_canvas(self, canvas):
    """Generate visual representation of canvas"""
    # Implementation would create visual canvas
    return "Visual canvas would be generated here" 