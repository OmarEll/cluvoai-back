from typing import List, Optional, Dict, Any
from datetime import datetime

from core.database import get_users_collection
from core.analysis_models import AnalysisType


class FeatureOrchestrationService:
    """
    Service to orchestrate features and track completion for intelligent context sharing
    """
    
    async def mark_analysis_completed(
        self, 
        user_id: str, 
        idea_id: str, 
        analysis_type: AnalysisType
    ) -> bool:
        """
        Mark an analysis as completed for a business idea
        """
        try:
            users_collection = await get_users_collection()
            
            # Map analysis type to completion flag
            analysis_mapping = {
                AnalysisType.COMPETITOR: "competitor",
                AnalysisType.PERSONA: "persona", 
                AnalysisType.MARKET_SIZING: "market_sizing",
                AnalysisType.BUSINESS_MODEL: "business_model",
                AnalysisType.BUSINESS_MODEL_CANVAS: "business_model_canvas"
            }
            
            analysis_key = analysis_mapping.get(analysis_type)
            if not analysis_key:
                print(f"Unknown analysis type: {analysis_type}")
                return False
            
            # Update the business idea's completed_analyses array
            result = await users_collection.update_one(
                {
                    "_id": user_id,
                    "ideas.id": idea_id
                },
                {
                    "$addToSet": {
                        "ideas.$.completed_analyses": analysis_key
                    },
                    "$set": {
                        "ideas.$.updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                print(f"✅ Marked {analysis_key} analysis as completed for idea {idea_id}")
                return True
            else:
                print(f"❌ Failed to mark {analysis_key} analysis as completed for idea {idea_id}")
                return False
                
        except Exception as e:
            print(f"Error marking analysis as completed: {e}")
            return False
    
    async def get_completed_analyses(
        self, 
        user_id: str, 
        idea_id: str
    ) -> List[str]:
        """
        Get list of completed analyses for a business idea
        """
        try:
            users_collection = await get_users_collection()
            
            user = await users_collection.find_one(
                {"_id": user_id},
                {"ideas": {"$elemMatch": {"id": idea_id}}}
            )
            
            if user and user.get("ideas"):
                idea = user["ideas"][0]
                return idea.get("completed_analyses", [])
            
            return []
            
        except Exception as e:
            print(f"Error getting completed analyses: {e}")
            return []
    
    async def get_analysis_dependencies(
        self, 
        analysis_type: AnalysisType
    ) -> List[str]:
        """
        Get the dependencies (required prior analyses) for a given analysis type
        """
        dependencies = {
            AnalysisType.COMPETITOR: [],  # No dependencies
            AnalysisType.PERSONA: [],     # No dependencies (can use competitor context if available)
            AnalysisType.MARKET_SIZING: []  # No dependencies (but benefits from both competitor and persona)
        }
        
        return dependencies.get(analysis_type, [])
    
    async def get_context_for_analysis(
        self, 
        user_id: str, 
        idea_id: str, 
        analysis_type: AnalysisType
    ) -> Dict[str, Any]:
        """
        Get available context from completed analyses for the current analysis
        """
        context = {}
        
        try:
            completed_analyses = await self.get_completed_analyses(user_id, idea_id)
            
            # Import here to avoid circular imports
            from services.analysis_storage_service import analysis_storage_service
            
            # Get competitor context if available
            if "competitor" in completed_analyses and analysis_type != AnalysisType.COMPETITOR:
                try:
                    competitor_analysis = await analysis_storage_service.get_user_analysis(
                        user_id, idea_id, AnalysisType.COMPETITOR, include_feedback=False
                    )
                    if competitor_analysis:
                        context["competitor_analysis"] = competitor_analysis
                        print(f"🔗 Added competitor context for {analysis_type.value} analysis")
                except Exception as e:
                    print(f"Error getting competitor context: {e}")
            
            # Get persona context if available
            if "persona" in completed_analyses and analysis_type != AnalysisType.PERSONA:
                try:
                    persona_analysis = await analysis_storage_service.get_user_analysis(
                        user_id, idea_id, AnalysisType.PERSONA, include_feedback=False
                    )
                    if persona_analysis:
                        context["persona_analysis"] = persona_analysis
                        print(f"🔗 Added persona context for {analysis_type.value} analysis")
                except Exception as e:
                    print(f"Error getting persona context: {e}")
            
            # Get market sizing context if available
            if "market_sizing" in completed_analyses and analysis_type != AnalysisType.MARKET_SIZING:
                try:
                    market_analysis = await analysis_storage_service.get_user_analysis(
                        user_id, idea_id, AnalysisType.MARKET_SIZING, include_feedback=False
                    )
                    if market_analysis:
                        context["market_sizing_analysis"] = market_analysis
                        print(f"🔗 Added market sizing context for {analysis_type.value} analysis")
                except Exception as e:
                    print(f"Error getting market sizing context: {e}")
            
        except Exception as e:
            print(f"Error getting context for analysis: {e}")
        
        return context
    
    async def get_recommended_next_analysis(
        self, 
        user_id: str, 
        idea_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get intelligent recommendation for the next analysis to run
        """
        try:
            completed_analyses = await self.get_completed_analyses(user_id, idea_id)
            
            # Get business idea details for context
            from services.user_management_service import user_management_service
            business_idea = await user_management_service.get_business_idea(user_id, idea_id)
            
            if not business_idea:
                return None
            
            # Define analysis priorities based on business stage and challenges
            recommendations = []
            
            # If no analyses completed
            if not completed_analyses:
                if business_idea.get("biggest_challenge") == "dont_know_if_anyone_needs_this":
                    recommendations.append({
                        "analysis_type": "persona_analysis",
                        "priority": "high",
                        "reason": "Validate customer needs first given your validation concerns",
                        "benefits": ["Understand if people actually need your solution", "Identify early adopters", "Validate problem-solution fit"]
                    })
                elif business_idea.get("biggest_challenge") == "dont_know_what_to_build_first":
                    recommendations.append({
                        "analysis_type": "competitor_analysis",
                        "priority": "high", 
                        "reason": "See what's already built and identify gaps",
                        "benefits": ["Understand existing solutions", "Find market gaps", "Avoid reinventing the wheel"]
                    })
                else:
                    recommendations.append({
                        "analysis_type": "competitor_analysis",
                        "priority": "high",
                        "reason": "Start with market landscape understanding",
                        "benefits": ["Understand competition", "Identify opportunities", "Learn pricing strategies"]
                    })
            
            # Progressive recommendations based on completion
            if "competitor" in completed_analyses and "persona" not in completed_analyses:
                recommendations.append({
                    "analysis_type": "persona_analysis",
                    "priority": "high",
                    "reason": "Enhance with competitor insights for better targeting",
                    "benefits": ["Use competitor data for persona refinement", "Identify underserved segments", "Understand customer behavior patterns"]
                })
            
            if "persona" in completed_analyses and "competitor" not in completed_analyses:
                recommendations.append({
                    "analysis_type": "competitor_analysis", 
                    "priority": "medium",
                    "reason": "Validate persona insights against market reality",
                    "benefits": ["See how competitors serve your personas", "Validate market demand", "Identify competitive gaps"]
                })
            
            if "competitor" in completed_analyses and "persona" in completed_analyses and "market_sizing" not in completed_analyses:
                recommendations.append({
                    "analysis_type": "market_sizing",
                    "priority": "high",
                    "reason": "Quantify opportunity with rich competitive and customer context",
                    "benefits": ["Accurate TAM/SAM/SOM with real data", "Revenue projections based on competitor pricing", "Investment-ready market analysis"]
                })
            
            if len(completed_analyses) >= 3:
                return {
                    "message": "All core analyses completed!",
                    "next_steps": [
                        "Review integrated insights across all analyses",
                        "Develop go-to-market strategy",
                        "Create business plan with validated assumptions",
                        "Consider advanced features like financial projections"
                    ]
                }
            
            return recommendations[0] if recommendations else None
            
        except Exception as e:
            print(f"Error getting next analysis recommendation: {e}")
            return None


# Create global instance
feature_orchestration_service = FeatureOrchestrationService() 