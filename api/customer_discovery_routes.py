import asyncio
import os
import tempfile
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Form, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import aiofiles

from core.customer_discovery_models import (
    CustomerInterview, InterviewCreateRequest, InterviewUpdateRequest,
    FileUploadRequest, TranscriptionRequest, AnalysisRequest,
    CustomerDiscoveryAnalysisRequest, InsightValidationRequest, BMCUpdateRequest,
    InterviewResponse, InterviewListResponse, TranscriptionResponse,
    AnalysisResponse, DashboardResponse, InsightResponse, BMCUpdateResponse,
    QuestionGeneratorResponse, InterviewType, InterviewStatus, FileType,
    CustomerSegment, ConfidenceLevel, InsightType, ScoreCategory
)
from services.auth_service import auth_service
from services.customer_discovery.transcription_service import transcription_service
from services.customer_discovery.analysis_service import analysis_service
from services.customer_discovery.bmc_update_service import bmc_update_service
from services.user_management_service import user_management_service

# Create router
router = APIRouter(prefix="/customer-discovery", tags=["Customer Discovery"])

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


# Interview Management Endpoints
@router.post("/interviews", response_model=InterviewResponse)
async def create_interview(
    request: InterviewCreateRequest,
    user_email: str = Depends(get_current_user_email)
):
    """
    Create a new customer interview
    """
    try:
        print(f"📝 Creating new interview for user: {user_email}")
        
        # Get user ID
        user = await auth_service.get_user_by_email(user_email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_id = str(user["_id"]) if isinstance(user, dict) else str(user.id)
        
        # Verify business idea exists
        try:
            idea = await user_management_service.get_business_idea(user_email, request.idea_id)
        except:
            raise HTTPException(status_code=404, detail="Business idea not found")
        
        # Create interview
        interview_id = str(uuid.uuid4())
        interview = CustomerInterview(
            id=interview_id,
            user_id=user_id,
            idea_id=request.idea_id,
            customer_profile=request.customer_profile,
            interview_type=request.interview_type,
            status=InterviewStatus.SCHEDULED,
            scheduled_at=request.scheduled_at,
            platform=request.platform,
            notes=request.notes,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # TODO: Save to database (implement storage service)
        # await interview_storage_service.create_interview(interview)
        
        print(f"✅ Interview created successfully: {interview_id}")
        
        return InterviewResponse(
            interview=interview,
            message="Interview created successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Interview creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create interview: {str(e)}"
        )


@router.get("/interviews", response_model=InterviewListResponse)
async def get_interviews(
    idea_id: Optional[str] = None,
    status: Optional[InterviewStatus] = None,
    segment: Optional[CustomerSegment] = None,
    page: int = 1,
    per_page: int = 20,
    user_email: str = Depends(get_current_user_email)
):
    """
    Get list of customer interviews with filtering
    """
    try:
        print(f"📋 Getting interviews for user: {user_email}")
        
        # Get user ID
        user = await auth_service.get_user_by_email(user_email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_id = str(user["_id"]) if isinstance(user, dict) else str(user.id)
        
        # TODO: Implement interview retrieval from database
        # For now, return empty list
        interviews = []
        total = 0
        
        return InterviewListResponse(
            interviews=interviews,
            total=total,
            page=page,
            per_page=per_page,
            message="Interviews retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Interview retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve interviews: {str(e)}"
        )


@router.get("/interviews/{interview_id}", response_model=InterviewResponse)
async def get_interview(
    interview_id: str,
    user_email: str = Depends(get_current_user_email)
):
    """
    Get specific interview by ID
    """
    try:
        print(f"🔍 Getting interview: {interview_id}")
        
        # Get user ID
        user = await auth_service.get_user_by_email(user_email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_id = str(user["_id"]) if isinstance(user, dict) else str(user.id)
        
        # TODO: Get interview from database
        # interview = await interview_storage_service.get_interview(interview_id, user_id)
        # if not interview:
        #     raise HTTPException(status_code=404, detail="Interview not found")
        
        # For now, return a placeholder
        raise HTTPException(status_code=404, detail="Interview not found")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Interview retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve interview: {str(e)}"
        )


@router.put("/interviews/{interview_id}", response_model=InterviewResponse)
async def update_interview(
    interview_id: str,
    request: InterviewUpdateRequest,
    user_email: str = Depends(get_current_user_email)
):
    """
    Update interview details
    """
    try:
        print(f"✏️ Updating interview: {interview_id}")
        
        # Get user ID
        user = await auth_service.get_user_by_email(user_email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_id = str(user["_id"]) if isinstance(user, dict) else str(user.id)
        
        # TODO: Update interview in database
        # updated_interview = await interview_storage_service.update_interview(
        #     interview_id, user_id, request
        # )
        
        # For now, return placeholder
        raise HTTPException(status_code=404, detail="Interview not found")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Interview update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update interview: {str(e)}"
        )


# File Upload and Transcription Endpoints
@router.post("/interviews/{interview_id}/upload")
async def upload_interview_file(
    interview_id: str,
    file: UploadFile = File(...),
    file_type: FileType = Form(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    user_email: str = Depends(get_current_user_email)
):
    """
    Upload audio, video, or transcript file for an interview
    """
    try:
        print(f"📁 Uploading file for interview: {interview_id}")
        
        # Get user ID
        user = await auth_service.get_user_by_email(user_email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_id = str(user["_id"]) if isinstance(user, dict) else str(user.id)
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="File name is required")
        
        # Check file size (25MB limit for Whisper API)
        max_size = 25 * 1024 * 1024  # 25MB
        if file.size and file.size > max_size:
            raise HTTPException(
                status_code=400, 
                detail=f"File size ({file.size} bytes) exceeds maximum allowed size (25MB)"
            )
        
        # Create uploads directory if it doesn't exist
        upload_dir = "uploads/interviews"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        saved_filename = f"{file_id}{file_extension}"
        file_path = os.path.join(upload_dir, saved_filename)
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        print(f"✅ File uploaded: {file_path}")
        
        # Create file record
        # TODO: Save file record to database
        
        # If it's an audio or video file, start transcription in background
        if file_type in [FileType.AUDIO, FileType.VIDEO]:
            background_tasks.add_task(
                transcribe_file_background,
                file_path, file_id, interview_id, file_type
            )
            message = "File uploaded successfully. Transcription started in background."
        else:
            message = "File uploaded successfully."
        
        return {
            "file_id": file_id,
            "file_path": file_path,
            "file_size": len(content),
            "message": message
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ File upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_file(
    request: TranscriptionRequest,
    user_email: str = Depends(get_current_user_email)
):
    """
    Transcribe an uploaded audio or video file
    """
    try:
        print(f"🎤 Starting transcription for file: {request.file_id}")
        
        # TODO: Get file info from database
        # file_info = await file_storage_service.get_file(request.file_id)
        # if not file_info:
        #     raise HTTPException(status_code=404, detail="File not found")
        
        # For now, assume file path (in real implementation, get from database)
        file_path = f"uploads/interviews/{request.file_id}.mp3"  # Placeholder
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Transcribe using OpenAI Whisper
        transcription = await transcription_service.transcribe_file(
            file_path=file_path,
            file_type=FileType.AUDIO,  # Would get from file record
            language=request.language,
            enable_speaker_labels=request.enable_speaker_labels,
            enable_timestamps=request.enable_timestamps
        )
        
        # TODO: Save transcription to database
        # await transcription_storage_service.save_transcription(transcription)
        
        return TranscriptionResponse(
            transcription=transcription,
            message="Transcription completed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Transcription failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to transcribe file: {str(e)}"
        )


# Analysis Endpoints
@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_interview(
    request: AnalysisRequest,
    user_email: str = Depends(get_current_user_email)
):
    """
    Analyze an interview to extract insights, pain points, and validation data
    """
    try:
        print(f"🧠 Analyzing interview: {request.interview_id}")
        
        # Get user ID
        user = await auth_service.get_user_by_email(user_email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_id = str(user["_id"]) if isinstance(user, dict) else str(user.id)
        
        # TODO: Get interview and transcription from database
        # interview = await interview_storage_service.get_interview(request.interview_id, user_id)
        # if not interview:
        #     raise HTTPException(status_code=404, detail="Interview not found")
        
        # transcription = await transcription_storage_service.get_latest_transcription(request.interview_id)
        # if not transcription:
        #     raise HTTPException(status_code=404, detail="No transcription found for this interview")
        
        # For now, create placeholder objects
        raise HTTPException(status_code=404, detail="Interview not found")
        
        # # Get business context
        # business_idea = await user_management_service.get_business_idea(user_email, interview.idea_id)
        # business_context = {
        #     "business_idea": business_idea.description,
        #     "title": business_idea.title
        # }
        
        # # Perform analysis
        # analysis = await analysis_service.analyze_interview(
        #     interview, transcription, business_context
        # )
        
        # # TODO: Save analysis to database
        # # await analysis_storage_service.save_analysis(analysis)
        
        # return AnalysisResponse(
        #     analysis=analysis,
        #     message="Interview analysis completed successfully"
        # )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Interview analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze interview: {str(e)}"
        )


@router.post("/analyze-idea", response_model=AnalysisResponse)
async def analyze_customer_discovery_for_idea(
    request: CustomerDiscoveryAnalysisRequest,
    user_email: str = Depends(get_current_user_email)
):
    """
    Perform customer discovery analysis for a business idea.
    Requires authentication and idea_id. Extracts all needed information from the idea.
    """
    try:
        print(f"🔍 Starting customer discovery analysis for idea: {request.idea_id}")
        
        # Get the business idea to extract all needed information
        business_idea = await user_management_service.get_business_idea(user_email, request.idea_id)
        if not business_idea:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business idea not found"
            )
        
        # For now, return a placeholder analysis
        # TODO: Implement actual customer discovery analysis logic
        from core.customer_discovery_models import InterviewAnalysis, InterviewScore, ExtractedInsight
        
        analysis = InterviewAnalysis(
            id=str(uuid.uuid4()),
            interview_id="placeholder",  # This would be generated from actual interviews
            overall_score=7.5,
            category_scores=[
                InterviewScore(
                    category=ScoreCategory.PROBLEM_CONFIRMATION,
                    score=8.0,
                    reasoning="Based on business idea analysis",
                    confidence=ConfidenceLevel.MEDIUM
                )
            ],
            key_insights=[
                ExtractedInsight(
                    id=str(uuid.uuid4()),
                    interview_id="placeholder",
                    type=InsightType.PAIN_POINT,
                    content="Customer discovery analysis completed",
                    quote="Analysis based on business idea",
                    context="Simplified analysis",
                    confidence=ConfidenceLevel.MEDIUM,
                    confidence_score=0.7,
                    impact_score=7.0
                )
            ],
            pain_points=["Need to conduct actual customer interviews"],
            validation_points=["Business idea structure is clear"],
            feature_requests=[],
            competitive_mentions=[],
            pricing_feedback=[],
            persona_updates={},
            bmc_updates={},
            follow_up_questions=[
                "What specific pain points do your target customers face?",
                "How do they currently solve these problems?",
                "What would they be willing to pay for a solution?"
            ],
            next_steps=[
                "Conduct customer interviews",
                "Validate problem-solution fit",
                "Test pricing assumptions"
            ],
            sentiment_analysis={"positive": 0.7, "neutral": 0.2, "negative": 0.1}
        )
        
        return AnalysisResponse(
            analysis=analysis,
            message="Customer discovery analysis completed successfully. Consider conducting actual customer interviews for more detailed insights."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Customer discovery analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Customer discovery analysis failed: {str(e)}"
        )


@router.get("/insights", response_model=InsightResponse)
async def get_insights(
    idea_id: Optional[str] = None,
    insight_type: Optional[InsightType] = None,
    confidence: Optional[ConfidenceLevel] = None,
    min_impact_score: Optional[float] = None,
    page: int = 1,
    per_page: int = 50,
    user_email: str = Depends(get_current_user_email)
):
    """
    Get extracted insights with filtering options
    """
    try:
        print(f"🔍 Getting insights for user: {user_email}")
        
        # Get user ID
        user = await auth_service.get_user_by_email(user_email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_id = str(user["_id"]) if isinstance(user, dict) else str(user.id)
        
        # TODO: Get insights from database with filtering
        # insights = await insight_storage_service.get_insights(
        #     user_id=user_id,
        #     idea_id=idea_id,
        #     insight_type=insight_type,
        #     confidence=confidence,
        #     min_impact_score=min_impact_score,
        #     page=page,
        #     per_page=per_page
        # )
        
        # For now, return empty list
        insights = []
        
        return InsightResponse(
            insights=insights,
            total=len(insights),
            message="Insights retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Insight retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve insights: {str(e)}"
        )


# BMC Update Endpoints
@router.post("/bmc-update", response_model=BMCUpdateResponse)
async def update_bmc_from_insights(
    request: BMCUpdateRequest,
    user_email: str = Depends(get_current_user_email)
):
    """
    Update Business Model Canvas based on customer discovery insights
    """
    try:
        print(f"🔄 Updating BMC from {len(request.insight_ids)} insights")
        
        # Get user ID
        user = await auth_service.get_user_by_email(user_email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_id = str(user["_id"]) if isinstance(user, dict) else str(user.id)
        
        # TODO: Get insights from database
        # insights = await insight_storage_service.get_insights_by_ids(request.insight_ids, user_id)
        # if not insights:
        #     raise HTTPException(status_code=404, detail="No insights found")
        
        # # Get idea ID from insights
        # idea_id = insights[0].interview_id  # You'd need to get this from interview
        
        # # Update BMC
        # result = await bmc_update_service.analyze_and_update_bmc(
        #     user_id=user_id,
        #     idea_id=idea_id,
        #     insights=insights,
        #     preview_only=request.preview_only
        # )
        
        # For now, return placeholder
        result = {
            "preview": None,
            "applied_updates": None,
            "affected_sections": [],
            "message": "BMC update service not yet connected to database"
        }
        
        return BMCUpdateResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ BMC update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update BMC: {str(e)}"
        )


# Dashboard and Analytics Endpoints
@router.get("/dashboard/{idea_id}", response_model=DashboardResponse)
async def get_discovery_dashboard(
    idea_id: str,
    user_email: str = Depends(get_current_user_email)
):
    """
    Get customer discovery dashboard with metrics and insights
    """
    try:
        print(f"📊 Getting discovery dashboard for idea: {idea_id}")
        
        # Get user ID
        user = await auth_service.get_user_by_email(user_email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_id = str(user["_id"]) if isinstance(user, dict) else str(user.id)
        
        # TODO: Calculate dashboard metrics from database
        # dashboard = await dashboard_service.calculate_dashboard_metrics(user_id, idea_id)
        
        # For now, return placeholder dashboard
        from core.customer_discovery_models import DiscoveryDashboard
        dashboard = DiscoveryDashboard(
            user_id=user_id,
            idea_id=idea_id,
            total_interviews=0,
            target_interviews=15,
            progress_percentage=0.0,
            quality_score=0.0,
            validation_score=0.0,
            response_rate=0.0,
            avg_duration=0.0,
            problem_confirmation=0.0,
            solution_interest=0.0,
            willingness_to_pay=0.0,
            referral_willingness=0.0,
            risk_level="low"
        )
        
        return DashboardResponse(
            dashboard=dashboard,
            message="Dashboard retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Dashboard retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve dashboard: {str(e)}"
        )


# AI Assistant Endpoints
@router.post("/generate-questions", response_model=QuestionGeneratorResponse)
async def generate_interview_questions(
    interview_type: InterviewType,
    customer_segment: Optional[CustomerSegment] = None,
    context: Optional[str] = None,
    user_email: str = Depends(get_current_user_email)
):
    """
    Generate AI-powered interview questions tailored to the context
    """
    try:
        print(f"🤖 Generating questions for {interview_type}")
        
        # Generate questions based on type and context
        questions = await generate_contextual_questions(
            interview_type, customer_segment, context
        )
        
        return QuestionGeneratorResponse(
            questions=questions,
            interview_type=interview_type,
            segment=customer_segment,
            context=context or "General customer discovery",
            message="Questions generated successfully"
        )
        
    except Exception as e:
        print(f"❌ Question generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate questions: {str(e)}"
        )


# Utility Endpoints
@router.get("/options/interview-types")
async def get_interview_type_options():
    """Get available interview types"""
    return {
        "interview_types": [
            {"value": item.value, "label": item.value.replace("_", " ").title()}
            for item in InterviewType
        ]
    }


@router.get("/options/customer-segments")
async def get_customer_segment_options():
    """Get available customer segments"""
    return {
        "customer_segments": [
            {"value": item.value, "label": item.value.replace("_", " ").title()}
            for item in CustomerSegment
        ]
    }


@router.get("/options/insight-types")
async def get_insight_type_options():
    """Get available insight types"""
    return {
        "insight_types": [
            {"value": item.value, "label": item.value.replace("_", " ").title()}
            for item in InsightType
        ]
    }


# Background Tasks
async def transcribe_file_background(
    file_path: str,
    file_id: str,
    interview_id: str,
    file_type: FileType
):
    """
    Background task to transcribe uploaded files
    """
    try:
        print(f"🎤 Background transcription started for file: {file_id}")
        
        # Transcribe the file
        transcription = await transcription_service.transcribe_file(
            file_path=file_path,
            file_type=file_type,
            language="en",
            enable_speaker_labels=True,
            enable_timestamps=True
        )
        
        # TODO: Save transcription to database
        # await transcription_storage_service.save_transcription(transcription)
        
        # TODO: Update interview status
        # await interview_storage_service.update_status(interview_id, InterviewStatus.TRANSCRIBED)
        
        print(f"✅ Background transcription completed for file: {file_id}")
        
    except Exception as e:
        print(f"❌ Background transcription failed for file {file_id}: {e}")


# Helper Functions
async def generate_contextual_questions(
    interview_type: InterviewType,
    customer_segment: Optional[CustomerSegment] = None,
    context: Optional[str] = None
) -> List[str]:
    """
    Generate contextual interview questions
    """
    base_questions = {
        InterviewType.PROBLEM_VALIDATION: [
            "Can you walk me through the last time you experienced this problem?",
            "What's the most frustrating part about your current solution?",
            "How much time does this problem cost you per week?",
            "What have you tried before that didn't work?",
            "On a scale of 1-10, how urgent is solving this for you?",
            "Who else is affected by this problem?",
            "What would need to change for this to not be a problem anymore?"
        ],
        InterviewType.SOLUTION_VALIDATION: [
            "If you could wave a magic wand and solve this perfectly, what would that look like?",
            "What features would be essential vs nice-to-have?",
            "How would you prefer to interact with this solution?",
            "What would make you choose this over your current solution?",
            "What concerns would you have about adopting this solution?",
            "How would you measure success with this solution?",
            "What would prevent you from using this solution?"
        ],
        InterviewType.CUSTOMER_DEVELOPMENT: [
            "What does a typical day look like for you?",
            "What are your biggest goals right now?",
            "What tools or services do you currently use for this?",
            "How do you typically discover new solutions?",
            "What factors influence your purchasing decisions?",
            "Who else is involved in decision-making?",
            "What's your budget range for solving this type of problem?"
        ],
        InterviewType.USER_TESTING: [
            "What's your first impression of this?",
            "Can you show me how you would use this feature?",
            "What's confusing or unclear about this?",
            "What would you expect to happen next?",
            "How does this compare to what you currently use?",
            "What would make this more useful for you?",
            "Would you recommend this to others? Why or why not?"
        ],
        InterviewType.MARKET_RESEARCH: [
            "How big do you think this market is?",
            "Who are the main players in this space?",
            "What trends are you seeing in this industry?",
            "What's driving change in this market?",
            "Where do you see opportunities for innovation?",
            "What barriers exist for new entrants?",
            "How do you stay informed about this industry?"
        ]
    }
    
    questions = base_questions.get(interview_type, [
        "Can you tell me about your experience with this?",
        "What challenges do you face in this area?",
        "How do you currently handle this situation?",
        "What would an ideal solution look like to you?",
        "What questions do you have for me?"
    ])
    
    # Add segment-specific questions if applicable
    if customer_segment == CustomerSegment.BUSY_PARENTS:
        questions.extend([
            "How does this fit into your family routine?",
            "What time constraints do you face?",
            "How do you balance this with other priorities?"
        ])
    elif customer_segment == CustomerSegment.REMOTE_WORKERS:
        questions.extend([
            "How does remote work affect this challenge?",
            "What tools do you use for productivity?",
            "How do you collaborate with your team on this?"
        ])
    
    return questions[:8]  # Return top 8 questions 