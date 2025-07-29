from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class FeatureType(str, Enum):
    COMPETITOR_ANALYSIS = "competitor"
    PERSONA_ANALYSIS = "persona"
    MARKET_SIZING = "market_sizing"
    BUSINESS_MODEL = "business_model"
    BUSINESS_MODEL_CANVAS = "business_model_canvas"
    CUSTOMER_DISCOVERY = "customer_discovery"
    GENERAL = "general"


class ChatMessage(BaseModel):
    """Individual chat message"""
    id: Optional[str] = None
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    feature_context: Optional[FeatureType] = None
    metadata: Optional[Dict[str, Any]] = None


class ConversationHistory(BaseModel):
    """Complete conversation history for a business idea"""
    id: Optional[str] = None
    user_id: str
    idea_id: str
    messages: List[ChatMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    total_messages: int = 0
    last_activity: datetime = Field(default_factory=datetime.utcnow)


class ChatRequest(BaseModel):
    """Request for sending a chat message"""
    idea_id: str = Field(..., description="Business idea ID", example="3df48626-0610-41c3-8080-8ebd93857390")
    message: str = Field(..., description="User message", example="What are the key insights from my competitor analysis?")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for continuing a chat")


class ChatResponse(BaseModel):
    """Response from the chat API"""
    conversation_id: str
    message_id: str
    response: str
    feature_context: Optional[FeatureType] = None
    suggested_questions: List[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.8)
    message: str = "Chat response generated successfully"


class ConversationListResponse(BaseModel):
    """Response for listing conversations"""
    conversations: List[Dict[str, Any]] = Field(default_factory=list)
    total_conversations: int = 0
    message: str = "Conversations retrieved successfully"


class ConversationDetailResponse(BaseModel):
    """Response for getting conversation details"""
    conversation: ConversationHistory
    message: str = "Conversation details retrieved successfully"


class FeatureContext(BaseModel):
    """Context from a specific feature analysis"""
    feature_type: FeatureType
    analysis_id: str
    content: Dict[str, Any]
    relevance_score: float = Field(ge=0.0, le=1.0)
    last_updated: datetime


class ChatContext(BaseModel):
    """Complete context for chat processing"""
    business_idea: Dict[str, Any]
    relevant_features: List[FeatureContext] = Field(default_factory=list)
    conversation_history: List[ChatMessage] = Field(default_factory=list)
    user_preferences: Optional[Dict[str, Any]] = None


class ChatAnalysisResult(BaseModel):
    """Result of chat analysis and context gathering"""
    detected_feature: Optional[FeatureType] = None
    confidence: float = Field(ge=0.0, le=1.0)
    relevant_context: List[FeatureContext] = Field(default_factory=list)
    suggested_actions: List[str] = Field(default_factory=list)
    response_strategy: str = "contextual_response" 