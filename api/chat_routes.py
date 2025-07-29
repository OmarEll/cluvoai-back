from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional

from core.chat_models import (
    ChatRequest, ChatResponse, ConversationHistory, 
    ConversationListResponse, ConversationDetailResponse
)
from core.user_models import UserInDB
from api.auth_routes import get_current_user
from services.chat_service import chat_service
from services.user_management_service import user_management_service

# Create router
router = APIRouter(prefix="/chat", tags=["Business Idea Chat"])

# Security
security = HTTPBearer()

# Removed problematic function - using get_current_user from auth_routes instead


@router.post("/test-chat")
async def test_chat(request: dict):
    """
    Test chat endpoint without authentication for testing HTML formatting
    """
    try:
        # Simple test response in HTML format
        test_response = """<div>
<h3>🤖 Chat API Test Response</h3>
<p><strong>Status:</strong> Chat API is working perfectly!</p>
<p><strong>HTML Formatting:</strong> <em>Enabled and functional</em></p>

<h3>📋 Features Available:</h3>
<ul>
<li><strong>Intent Detection</strong> - Automatically detects what you're asking about</li>
<li><strong>HTML Responses</strong> - Formatted for beautiful display</li>
<li><strong>Smart Suggestions</strong> - Context-aware follow-up questions</li>
<li><strong>Business Context</strong> - Pulls data from your analyses</li>
</ul>

<h3>💡 Example Usage:</h3>
<p>Ask questions like:</p>
<ul>
<li>"What are the key insights from my competitor analysis?"</li>
<li>"Tell me about my target customers and personas"</li>
<li>"What's my market opportunity?"</li>
<li>"How should I price my product?"</li>
</ul>

<p><em>The chat API is ready for frontend integration!</em> 🚀</p>
</div>"""
        
        return {
            "response": test_response,
            "message": "Chat API test successful",
            "html_formatted": True,
            "suggested_questions": [
                "How does the intent detection work?",
                "What types of business questions can I ask?",
                "How do I integrate this with my frontend?"
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat test failed: {str(e)}")


@router.post("/send", response_model=ChatResponse)
async def send_chat_message(
    request: ChatRequest,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Send a chat message and get AI response with business context
    """
    try:
        print(f"💬 Processing chat message for user: {current_user.email}")
        
        # Verify business idea exists and user has access
        try:
            business_idea = await user_management_service.get_business_idea(current_user.email, request.idea_id)
            if not business_idea:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Business idea not found or access denied"
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business idea not found or access denied"
            )
        
        # Send message through chat service
        response = await chat_service.send_message(
            user_id=current_user.id,
            idea_id=request.idea_id,
            message=request.message,
            conversation_id=request.conversation_id
        )
        
        print(f"✅ Chat response generated for user: {current_user.email}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in chat message processing: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process chat message: {str(e)}"
        )


@router.get("/conversations", response_model=ConversationListResponse)
async def get_conversations(
    idea_id: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get all conversations for the current user
    """
    try:
        conversations = await chat_service.get_user_conversations(current_user.id, idea_id)
        
        return ConversationListResponse(
            conversations=conversations,
            total_conversations=len(conversations),
            message=f"Retrieved {len(conversations)} conversations successfully"
        )
        
    except Exception as e:
        print(f"❌ Error retrieving conversations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve conversations: {str(e)}"
        )


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Get detailed conversation history
    """
    try:
        conversation = await chat_service.get_conversation_history(conversation_id)
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Verify user owns this conversation
        if conversation.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this conversation"
            )
        
        return ConversationDetailResponse(
            conversation=conversation,
            message="Conversation details retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error retrieving conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve conversation: {str(e)}"
        )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Delete a conversation
    """
    try:
        conversation = await chat_service.get_conversation_history(conversation_id)
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Verify user owns this conversation
        if conversation.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this conversation"
            )
        
        # Delete conversation (currently just removes from memory)
        if conversation_id in chat_service.conversations:
            del chat_service.conversations[conversation_id]
        
        return {"message": "Conversation deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete conversation: {str(e)}"
        )


@router.get("/health")
async def chat_health():
    """
    Chat service health check
    """
    try:
        active_conversations = len(chat_service.conversations)
        
        return {
            "status": "healthy",
            "service": "chat",
            "active_conversations": active_conversations,
            "message": "Chat service is operational"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat service health check failed: {str(e)}"
        ) 