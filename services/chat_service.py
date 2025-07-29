import uuid
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.tools import tool
from langchain_core.runnables import RunnableLambda
import re

from core.chat_models import (
    ChatMessage, ConversationHistory, FeatureType, ChatContext, 
    ChatAnalysisResult, MessageRole, ChatResponse
)
from core.analysis_models import AnalysisType
from services.analysis_storage_service import analysis_storage_service
from services.user_management_service import user_management_service
from config.settings import settings


class ChatService:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=0.7,
            api_key=settings.openai_api_key
        )
        self.conversations = {}  # In-memory storage for conversations
    

    
    async def analyze_user_intent_simple(self, user_message: str) -> ChatAnalysisResult:
        """Analyze user intent and detect relevant features"""
        
        # Keywords for feature detection
        feature_keywords = {
            FeatureType.COMPETITOR_ANALYSIS: [
                "competitor", "competition", "rival", "market share", "competitive advantage",
                "competitors", "competitive landscape", "market position"
            ],
            FeatureType.PERSONA_ANALYSIS: [
                "persona", "customer", "target audience", "user", "demographics",
                "customer profile", "target market", "audience"
            ],
            FeatureType.MARKET_SIZING: [
                "market size", "market opportunity", "TAM", "SAM", "SOM",
                "market potential", "addressable market", "market growth"
            ],
            FeatureType.BUSINESS_MODEL: [
                "business model", "revenue model", "pricing", "monetization",
                "revenue streams", "business strategy", "profitability"
            ],
            FeatureType.BUSINESS_MODEL_CANVAS: [
                "canvas", "business model canvas", "BMC", "value proposition",
                "customer segments", "key resources", "cost structure"
            ],
            FeatureType.CUSTOMER_DISCOVERY: [
                "customer discovery", "validation", "interview", "feedback",
                "customer research", "user research", "validation"
            ]
        }
        
        detected_feature = FeatureType.GENERAL
        max_confidence = 0.0
        
        for feature, keywords in feature_keywords.items():
            confidence = sum(1 for keyword in keywords if keyword.lower() in user_message.lower())
            if confidence > max_confidence:
                max_confidence = confidence
                detected_feature = feature
        
        confidence_score = min(max_confidence / 3.0, 1.0)  # Normalize confidence
        
        return ChatAnalysisResult(
            detected_feature=detected_feature,
            confidence=confidence_score,
            response_strategy="contextual_response"
        )
    
    async def gather_relevant_context_simple(self, user_id: str, idea_id: str, detected_feature: FeatureType) -> List[Dict[str, Any]]:
        """Gather relevant context from saved analyses"""
        relevant_contexts = []
        
        # Map feature types to analysis types
        feature_to_analysis = {
            FeatureType.COMPETITOR_ANALYSIS: "competitor",
            FeatureType.PERSONA_ANALYSIS: "persona",
            FeatureType.MARKET_SIZING: "market_sizing",
            FeatureType.BUSINESS_MODEL: "business_model",
            FeatureType.BUSINESS_MODEL_CANVAS: "business_model_canvas",
            FeatureType.CUSTOMER_DISCOVERY: "customer_discovery"
        }
        
        # Get specific analysis if detected
        if detected_feature in feature_to_analysis:
            analysis_type = feature_to_analysis[detected_feature]
            try:
                # Directly query the saved_analyses collection
                from core.database import get_saved_analyses_collection
                collection = get_saved_analyses_collection()
                
                # Find the most recent analysis for this idea and type
                analysis = await collection.find_one(
                    {"idea_id": idea_id, "analysis_type": analysis_type},
                    sort=[("created_at", -1)]
                )
                
                if analysis:
                    relevant_contexts.append({
                        "feature_type": detected_feature,
                        "analysis_id": str(analysis.get("_id")),
                        "content": analysis.get("result", {}),
                        "relevance_score": 0.9,
                        "last_updated": analysis.get("created_at")
                    })
                    print(f"Found {detected_feature} analysis for idea {idea_id}")
                else:
                    print(f"No {detected_feature} analysis found for idea {idea_id}")
            except Exception as e:
                print(f"Error gathering context for {detected_feature}: {e}")
        
        # Also get general business idea context
        try:
            business_idea = await user_management_service.get_business_idea_by_id(idea_id)
            if business_idea:
                relevant_contexts.append({
                    "feature_type": FeatureType.GENERAL,
                    "analysis_id": "business_idea",
                    "content": {
                        "title": business_idea.title,
                        "description": business_idea.description,
                        "target_market": business_idea.target_market,
                        "industry": business_idea.industry,
                        "current_stage": business_idea.current_stage
                    },
                    "relevance_score": 1.0,
                    "last_updated": business_idea.created_at
                })
                print(f"Found business idea context for idea {idea_id}")
        except Exception as e:
            print(f"Error gathering business idea context: {e}")
        
        return relevant_contexts
    
    def extract_analysis_content(self, analysis, feature_type: FeatureType) -> Dict[str, Any]:
        """Extract relevant content from analysis based on feature type"""
        content = {}
        
        if feature_type == FeatureType.COMPETITOR_ANALYSIS and hasattr(analysis, 'competitor_report'):
            report = analysis.competitor_report
            content = {
                "total_competitors": len(report.competitors) if hasattr(report, 'competitors') else 0,
                "market_gaps": report.market_gaps if hasattr(report, 'market_gaps') else [],
                "key_insights": report.key_insights if hasattr(report, 'key_insights') else [],
                "recommendations": report.recommendations if hasattr(report, 'recommendations') else []
            }
        
        elif feature_type == FeatureType.PERSONA_ANALYSIS and hasattr(analysis, 'persona_report'):
            report = analysis.persona_report
            content = {
                "personas": report.personas if hasattr(report, 'personas') else [],
                "key_insights": report.key_insights if hasattr(report, 'key_insights') else [],
                "recommendations": report.recommendations if hasattr(report, 'recommendations') else []
            }
        
        elif feature_type == FeatureType.MARKET_SIZING and hasattr(analysis, 'market_sizing_report'):
            report = analysis.market_sizing_report
            content = {
                "tam_sam_som": report.tam_sam_som if hasattr(report, 'tam_sam_som') else {},
                "market_overview": report.market_overview if hasattr(report, 'market_overview') else {},
                "revenue_projections": report.revenue_projections if hasattr(report, 'revenue_projections') else []
            }
        
        elif feature_type == FeatureType.BUSINESS_MODEL and hasattr(analysis, 'business_model_report'):
            report = analysis.business_model_report
            content = {
                "primary_recommendation": report.primary_recommendation if hasattr(report, 'primary_recommendation') else {},
                "profitability_projections": report.profitability_projections if hasattr(report, 'profitability_projections') else []
            }
        
        elif feature_type == FeatureType.BUSINESS_MODEL_CANVAS and hasattr(analysis, 'business_model_canvas_report'):
            canvas = analysis.business_model_canvas_report
            content = {
                "customer_segments": canvas.customer_segments if hasattr(canvas, 'customer_segments') else {},
                "value_propositions": canvas.value_propositions if hasattr(canvas, 'value_propositions') else {},
                "revenue_streams": canvas.revenue_streams if hasattr(canvas, 'revenue_streams') else {}
            }
        
        return content
    
    async def generate_contextual_response_simple(self, user_message: str, contexts: List[Dict[str, Any]], conversation_history: List[ChatMessage]) -> str:
        """Generate contextual response using LangChain"""
        
        # Create system prompt
        system_prompt = self.create_system_prompt(contexts)
        print(f"System prompt length: {len(system_prompt)} characters")
        print(f"Number of contexts: {len(contexts)}")
        
        # Create conversation history for context
        messages = [SystemMessage(content=system_prompt)]
        
        # Add conversation history (last 10 messages)
        for msg in conversation_history[-10:]:
            if msg.role == MessageRole.USER:
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == MessageRole.ASSISTANT:
                messages.append(AIMessage(content=msg.content))
        
        # Add current user message
        messages.append(HumanMessage(content=user_message))
        
        print(f"Total messages to send to LLM: {len(messages)}")
        
        # Generate response
        try:
            print("Attempting to call OpenAI API...")
            response = await self.llm.ainvoke(messages)
            print("OpenAI API call successful!")
            return response.content
        except Exception as e:
            print(f"Error generating response: {e}")
            print(f"Error type: {type(e)}")
            
            # Provide a contextual fallback response based on available context
            if contexts:
                context_info = []
                for ctx in contexts:
                    if ctx.get("feature_type") != FeatureType.GENERAL:
                        context_info.append(f"<li>{ctx['feature_type']} analysis data available</li>")
                
                if context_info:
                    return f"""<div>
<h3>Available Analysis Data</h3>
<p>I found some relevant analysis data for your question. Here's what I have available:</p>
<ul>
{''.join(context_info)}
</ul>
<p><em>Please try asking a more specific question about this data, or run the analysis first if you haven't already.</em></p>
</div>"""
            
            return """<div>
<h3>No Analysis Data Available</h3>
<p>I don't have any relevant analysis data for your question yet. Please run the appropriate analysis first:</p>
<ul>
<li><strong>Competitor Analysis</strong> - to understand your market landscape</li>
<li><strong>Persona Analysis</strong> - to identify your target customers</li>
<li><strong>Market Sizing</strong> - to assess market opportunity</li>
<li><strong>Business Model</strong> - to define your revenue strategy</li>
<li><strong>Business Model Canvas</strong> - to map your business components</li>
<li><strong>Customer Discovery</strong> - to validate your assumptions</li>
</ul>
<p><em>Once you have the analysis results, I can provide much more specific and actionable insights!</em></p>
</div>"""
    
    def create_system_prompt(self, contexts: List[Dict[str, Any]]) -> str:
        """Create system prompt with business context"""
        prompt = """You are an AI business advisor specialized in helping entrepreneurs with their business ideas. You have access to detailed analysis results and should provide specific, actionable insights based on the available data.

IMPORTANT RULES:
1. Only discuss the specific business idea the user is asking about
2. Base your responses on the provided analysis data
3. Be specific and actionable in your advice
4. If you don't have relevant data, suggest running the appropriate analysis
5. Stay focused on business strategy and growth opportunities
6. Use a professional but friendly tone
7. ALWAYS format your response in HTML with proper tags for better readability

RESPONSE FORMAT:
- Use <h3> for section headers
- Use <p> for paragraphs
- Use <ul> and <li> for lists
- Use <strong> for emphasis
- Use <em> for important points
- Use <div> for sections
- Use <span> for inline styling

BUSINESS IDEA CONTEXT:
"""
        
        # Add business idea context
        for context in contexts:
            if context["feature_type"] == FeatureType.GENERAL:
                idea_content = context["content"]
                prompt += f"""
<div>
<h3>Business Idea Overview</h3>
<p><strong>Title:</strong> {idea_content.get('title', 'N/A')}</p>
<p><strong>Description:</strong> {idea_content.get('description', 'N/A')}</p>
<p><strong>Target Market:</strong> {idea_content.get('target_market', 'N/A')}</p>
<p><strong>Industry:</strong> {idea_content.get('industry', 'N/A')}</p>
<p><strong>Current Stage:</strong> {idea_content.get('current_stage', 'N/A')}</p>
</div>
"""
                break
        
        # Add analysis context (simplified to avoid very long prompts)
        for context in contexts:
            if context["feature_type"] != FeatureType.GENERAL:
                feature_name = context["feature_type"].value.replace("_", " ").title()
                prompt += f"\n<h3>{feature_name} Analysis Results</h3>\n"
                
                # Limit the content to avoid very long prompts
                content = context["content"]
                if isinstance(content, dict):
                    # Take only key fields and limit length
                    simplified_content = {}
                    for key, value in content.items():
                        if isinstance(value, str) and len(value) > 500:
                            simplified_content[key] = value[:500] + "..."
                        else:
                            simplified_content[key] = value
                    prompt += f"<pre>{json.dumps(simplified_content, indent=2, default=str)}</pre>"
                else:
                    prompt += f"<pre>{str(content)[:1000] + '...' if len(str(content)) > 1000 else str(content)}</pre>"
                prompt += "\n"
        
        prompt += """
Based on this context, provide specific, actionable advice in HTML format. If the user asks about an analysis that hasn't been run yet, suggest they run that analysis first to get more detailed insights.

Remember to structure your response with proper HTML tags for better readability and visual appeal.
"""
        
        return prompt
    
    async def send_message(
        self, 
        user_id: str, 
        idea_id: str, 
        message: str, 
        conversation_id: Optional[str] = None
    ) -> ChatResponse:
        """Send a message and get response"""
        
        # Get or create conversation
        if conversation_id and conversation_id in self.conversations:
            conversation = self.conversations[conversation_id]
        else:
            conversation_id = str(uuid.uuid4())
            conversation = ConversationHistory(
                id=conversation_id,
                user_id=user_id,
                idea_id=idea_id
            )
            self.conversations[conversation_id] = conversation
        
        # Add user message
        user_message = ChatMessage(
            id=str(uuid.uuid4()),
            role=MessageRole.USER,
            content=message,
            timestamp=datetime.utcnow()
        )
        conversation.messages.append(user_message)
        
        # Analyze user intent and gather context
        analysis_result = None
        contexts = []
        response_content = ""
        
        try:
            # Analyze intent
            analysis_result = await self.analyze_user_intent_simple(message)
            
            # Gather context
            contexts = await self.gather_relevant_context_simple(user_id, idea_id, analysis_result.detected_feature)
            
            # Generate response
            response_content = await self.generate_contextual_response_simple(
                message, contexts, conversation.messages
            )
        except Exception as e:
            print(f"Error in chat processing: {e}")
            response_content = "I apologize, but I'm having trouble processing your request. Please try again."
            if analysis_result is None:
                analysis_result = ChatAnalysisResult(
                    detected_feature=FeatureType.GENERAL,
                    confidence=0.0,
                    response_strategy="fallback"
                )
        
        # Add assistant message
        assistant_message = ChatMessage(
            id=str(uuid.uuid4()),
            role=MessageRole.ASSISTANT,
            content=response_content,
            timestamp=datetime.utcnow(),
            feature_context=analysis_result.detected_feature
        )
        conversation.messages.append(assistant_message)
        
        # Update conversation
        conversation.total_messages = len(conversation.messages)
        conversation.last_activity = datetime.utcnow()
        conversation.updated_at = datetime.utcnow()
        
        # Generate suggested questions
        suggested_questions = self.generate_suggested_questions(
            analysis_result.detected_feature,
            contexts=contexts
        )
        
        return ChatResponse(
            conversation_id=conversation_id,
            message_id=assistant_message.id,
            response=response_content,
            feature_context=analysis_result.detected_feature,
            suggested_questions=suggested_questions,
            confidence_score=analysis_result.confidence
        )
    
    def generate_suggested_questions(self, detected_feature: Optional[FeatureType], contexts: List[Dict[str, Any]]) -> List[str]:
        """Generate suggested follow-up questions based on context"""
        questions = []
        
        if detected_feature == FeatureType.COMPETITOR_ANALYSIS:
            questions = [
                "What are the main competitive advantages I should focus on?",
                "How can I differentiate from my competitors?",
                "What market gaps should I target?"
            ]
        elif detected_feature == FeatureType.PERSONA_ANALYSIS:
            questions = [
                "What are the key pain points of my target customers?",
                "How should I position my product for my target audience?",
                "What features would be most valuable to my customers?"
            ]
        elif detected_feature == FeatureType.MARKET_SIZING:
            questions = [
                "What's my realistic market opportunity?",
                "How should I approach market entry?",
                "What's my path to capturing market share?"
            ]
        elif detected_feature == FeatureType.BUSINESS_MODEL:
            questions = [
                "What pricing strategy should I use?",
                "How can I optimize my revenue streams?",
                "What's my path to profitability?"
            ]
        else:
            questions = [
                "What's the next step I should focus on?",
                "What analysis would be most helpful right now?",
                "How can I validate my business assumptions?"
            ]
        
        return questions[:3]  # Return top 3 questions
    
    async def get_conversation_history(self, conversation_id: str) -> Optional[ConversationHistory]:
        """Get conversation history"""
        return self.conversations.get(conversation_id)
    
    async def get_user_conversations(self, user_id: str, idea_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all conversations for a user"""
        conversations = []
        for conv_id, conversation in self.conversations.items():
            if conversation.user_id == user_id:
                if idea_id is None or conversation.idea_id == idea_id:
                    conversations.append({
                        "id": conv_id,
                        "idea_id": conversation.idea_id,
                        "total_messages": conversation.total_messages,
                        "last_activity": conversation.last_activity,
                        "created_at": conversation.created_at
                    })
        
        return sorted(conversations, key=lambda x: x["last_activity"], reverse=True)


# Create singleton instance
chat_service = ChatService() 