import asyncio
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import uuid

from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from langchain.prompts import ChatPromptTemplate

from core.customer_discovery_models import ExtractedInsight, InsightType, ConfidenceLevel
from core.business_model_canvas_models import BusinessModelCanvas
from services.analysis_storage_service import analysis_storage_service
from services.business_model_canvas.canvas_generator_service import canvas_generator_service
from workflows.simple_business_model_canvas_workflow import simple_business_model_canvas_workflow
from core.analysis_models import AnalysisType
from config.settings import settings


class BMCUpdateService:
    """
    Service to automatically update Business Model Canvas based on customer discovery insights
    Provides intelligent updates while preserving existing validated content
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            openai_api_key=settings.openai_api_key,
            temperature=0.1
        )
        self.parser = JsonOutputParser()
        
        # Create BMC update prompt
        self.bmc_update_prompt = ChatPromptTemplate.from_template("""
        You are an expert business model strategist specializing in updating Business Model Canvases based on customer discovery insights.
        
        CURRENT BUSINESS MODEL CANVAS:
        {current_bmc}
        
        CUSTOMER DISCOVERY INSIGHTS:
        {insights}
        
        INSIGHT CONTEXT:
        - Total interviews analyzed: {total_interviews}
        - Insight confidence levels: {confidence_summary}
        - Most frequent pain points: {frequent_pain_points}
        - Validation signals: {validation_signals}
        
        TASK:
        Analyze the customer discovery insights and recommend specific updates to the Business Model Canvas.
        
        GUIDELINES:
        1. **Preserve Validated Content**: Only suggest changes where insights provide strong evidence
        2. **Prioritize High-Confidence Insights**: Weight updates based on insight confidence and frequency
        3. **Maintain Consistency**: Ensure updates across all nine building blocks remain coherent
        4. **Evidence-Based Changes**: Every update must be backed by specific customer quotes or patterns
        
        For each BMC section, provide:
        - **Recommended Updates**: Specific changes based on insights
        - **Evidence**: Customer quotes or patterns supporting the update
        - **Confidence Level**: How confident you are in this update (1-10)
        - **Impact Assessment**: How significant this change is for the business model
        
        BMC SECTIONS TO ANALYZE:
        
        1. **Customer Segments**
        - New segment characteristics discovered
        - Segment size indicators
        - Behavioral patterns and preferences
        
        2. **Value Propositions**
        - Pain points that need addressing
        - Benefits customers specifically mentioned
        - Value drivers customers emphasized
        
        3. **Channels**
        - Preferred communication methods mentioned
        - Customer touchpoint preferences
        - Distribution channel feedback
        
        4. **Customer Relationships**
        - Relationship type preferences
        - Support and service expectations
        - Community and engagement desires
        
        5. **Revenue Streams**
        - Pricing feedback and willingness to pay
        - Preferred payment models
        - Value-based pricing insights
        
        6. **Key Resources**
        - Resources customers expect you to have
        - Capabilities they consider essential
        - Technology or expertise requirements
        
        7. **Key Activities**
        - Activities customers value most
        - Processes they want improved
        - Service delivery expectations
        
        8. **Key Partnerships**
        - Partner suggestions from customers
        - Integration preferences
        - Ecosystem expectations
        
        9. **Cost Structure**
        - Cost considerations from customer perspective
        - Price sensitivity insights
        - Value vs cost trade-offs
        
        Return your analysis as JSON:
        {{
            "update_summary": {{
                "total_sections_updated": int,
                "confidence_score": float,
                "impact_level": "low|medium|high",
                "recommendation": "overall recommendation"
            }},
            "section_updates": {{
                "customer_segments": {{
                    "updates": {{
                        "characteristics": ["new trait 1", "new trait 2"],
                        "needs": ["updated need 1"],
                        "pain_points": ["validated pain 1"]
                    }},
                    "evidence": ["quote 1", "quote 2"],
                    "confidence": 8.5,
                    "impact": "high",
                    "reasoning": "explanation"
                }},
                "value_propositions": {{
                    "updates": {{
                        "benefits": ["refined benefit 1"],
                        "pain_points_solved": ["confirmed pain solution"],
                        "competitive_advantages": ["new advantage"]
                    }},
                    "evidence": ["supporting quote"],
                    "confidence": 9.0,
                    "impact": "high",
                    "reasoning": "explanation"
                }}
                // ... other sections as needed
            }},
            "new_insights": {{
                "market_opportunities": ["opportunity 1"],
                "risks_identified": ["risk 1"],
                "assumptions_validated": ["assumption 1"],
                "assumptions_invalidated": ["assumption 2"]
            }},
            "next_steps": {{
                "immediate_actions": ["action 1"],
                "further_validation_needed": ["area 1"],
                "additional_interviews_suggested": ["segment 1"]
            }}
        }}
        
        Be specific, evidence-based, and conservative in your recommendations. Only suggest changes where customer insights provide clear direction.
        """)
        
        # Create insight consolidation prompt
        self.insight_consolidation_prompt = ChatPromptTemplate.from_template("""
        You are analyzing multiple customer discovery insights to identify patterns and consolidate findings.
        
        INSIGHTS TO ANALYZE:
        {insights}
        
        TASK:
        1. Identify patterns and themes across insights
        2. Consolidate similar insights
        3. Rank insights by business impact and confidence
        4. Identify conflicting insights that need resolution
        
        Return consolidated analysis as JSON:
        {{
            "patterns": [
                {{
                    "theme": "pattern name",
                    "frequency": int,
                    "confidence": float,
                    "insights": ["insight 1", "insight 2"],
                    "business_impact": "low|medium|high"
                }}
            ],
            "conflicts": [
                {{
                    "description": "conflict description",
                    "conflicting_insights": ["insight 1", "insight 2"],
                    "resolution_needed": "how to resolve"
                }}
            ],
            "prioritized_insights": [
                {{
                    "insight": "insight description",
                    "priority_score": float,
                    "reasoning": "why this is high priority"
                }}
            ]
        }}
        """)
    
    async def analyze_and_update_bmc(
        self,
        user_id: str,
        idea_id: str,
        insights: List[ExtractedInsight],
        force_update: bool = False,
        preview_only: bool = False
    ) -> Dict[str, Any]:
        """
        Analyze insights and update the Business Model Canvas
        """
        try:
            print(f"🔄 Analyzing {len(insights)} insights for BMC updates")
            start_time = datetime.utcnow()
            
            # Get current BMC
            current_bmc = await self._get_current_bmc(user_id, idea_id)
            if not current_bmc:
                print("⚠️ No existing BMC found, cannot update")
                return {"error": "No existing Business Model Canvas found"}
            
            # Consolidate and prioritize insights
            consolidated_insights = await self._consolidate_insights(insights)
            
            # Prepare insight summary for analysis
            insight_summary = self._prepare_insight_summary(insights)
            
            # Get update recommendations from AI
            update_recommendations = await self._get_bmc_update_recommendations(
                current_bmc, insights, insight_summary
            )
            
            if preview_only:
                processing_time = (datetime.utcnow() - start_time).total_seconds()
                print(f"✅ BMC update preview generated in {processing_time:.2f} seconds")
                return {
                    "preview": update_recommendations,
                    "current_bmc": current_bmc.dict() if hasattr(current_bmc, 'dict') else current_bmc,
                    "insights_analyzed": len(insights),
                    "processing_time": processing_time
                }
            
            # Apply updates to BMC
            updated_bmc = await self._apply_updates_to_bmc(
                current_bmc, update_recommendations, insights
            )
            
            # Save updated BMC if not preview
            if not preview_only:
                await self._save_updated_bmc(user_id, idea_id, updated_bmc, insights)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            print(f"✅ BMC updated successfully in {processing_time:.2f} seconds")
            
            return {
                "updated_bmc": updated_bmc.dict() if hasattr(updated_bmc, 'dict') else updated_bmc,
                "recommendations": update_recommendations,
                "insights_applied": len(insights),
                "sections_updated": update_recommendations.get("update_summary", {}).get("total_sections_updated", 0),
                "confidence_score": update_recommendations.get("update_summary", {}).get("confidence_score", 0),
                "processing_time": processing_time
            }
            
        except Exception as e:
            print(f"❌ BMC update failed: {e}")
            raise Exception(f"Failed to update BMC: {str(e)}")
    
    async def validate_insight_impact(
        self,
        insight: ExtractedInsight,
        current_bmc: BusinessModelCanvas
    ) -> Dict[str, Any]:
        """
        Validate how a specific insight would impact the BMC
        """
        try:
            print(f"🔍 Validating impact of insight: {insight.type.value}")
            
            # Analyze specific insight impact
            impact_analysis = {
                "insight_id": insight.id,
                "insight_type": insight.type.value,
                "confidence": insight.confidence.value,
                "impact_score": insight.impact_score,
                "affected_sections": [],
                "recommended_changes": {},
                "validation_status": "pending"
            }
            
            # Map insight types to BMC sections
            section_mapping = {
                InsightType.PAIN_POINT: ["customer_segments", "value_propositions"],
                InsightType.VALIDATION_POINT: ["value_propositions", "customer_relationships"],
                InsightType.FEATURE_REQUEST: ["value_propositions", "key_activities"],
                InsightType.PRICING_FEEDBACK: ["revenue_streams", "cost_structure"],
                InsightType.COMPETITIVE_MENTION: ["value_propositions", "key_partnerships"],
                InsightType.MARKET_SIZE_INDICATOR: ["customer_segments", "revenue_streams"],
                InsightType.PERSONA_CHARACTERISTIC: ["customer_segments"],
                InsightType.BMC_UPDATE: ["all"]
            }
            
            # Determine affected sections
            if insight.type in section_mapping:
                impact_analysis["affected_sections"] = section_mapping[insight.type]
            
            # Analyze specific changes needed
            if insight.bmc_impact:
                impact_analysis["recommended_changes"] = insight.bmc_impact
            
            # Determine validation status based on confidence and impact
            if insight.confidence in [ConfidenceLevel.HIGH, ConfidenceLevel.VERY_HIGH] and insight.impact_score >= 7.0:
                impact_analysis["validation_status"] = "recommended"
            elif insight.confidence == ConfidenceLevel.MEDIUM and insight.impact_score >= 5.0:
                impact_analysis["validation_status"] = "consider"
            else:
                impact_analysis["validation_status"] = "low_priority"
            
            return impact_analysis
            
        except Exception as e:
            print(f"❌ Insight validation failed: {e}")
            return {"error": str(e)}
    
    async def batch_update_bmc(
        self,
        user_id: str,
        idea_id: str,
        interview_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Update BMC based on insights from multiple interviews
        """
        try:
            print(f"📊 Batch updating BMC from {len(interview_ids)} interviews")
            
            # Collect all insights from specified interviews
            all_insights = []
            
            for interview_id in interview_ids:
                # Get insights for this interview (this would be implemented in your storage service)
                # For now, we'll assume you have a method to get insights by interview ID
                insights = await self._get_insights_by_interview_id(interview_id)
                all_insights.extend(insights)
            
            if not all_insights:
                return {"error": "No insights found for specified interviews"}
            
            # Filter insights by confidence and impact
            high_confidence_insights = [
                insight for insight in all_insights
                if insight.confidence in [ConfidenceLevel.HIGH, ConfidenceLevel.VERY_HIGH]
                and insight.impact_score >= 6.0
            ]
            
            print(f"🎯 Using {len(high_confidence_insights)} high-confidence insights for update")
            
            # Perform BMC update
            result = await self.analyze_and_update_bmc(
                user_id, idea_id, high_confidence_insights, force_update=True
            )
            
            result["total_insights_analyzed"] = len(all_insights)
            result["high_confidence_insights_used"] = len(high_confidence_insights)
            result["source_interviews"] = interview_ids
            
            return result
            
        except Exception as e:
            print(f"❌ Batch BMC update failed: {e}")
            raise Exception(f"Failed to batch update BMC: {str(e)}")
    
    async def _get_current_bmc(self, user_id: str, idea_id: str) -> Optional[BusinessModelCanvas]:
        """
        Get the current Business Model Canvas for an idea
        """
        try:
            # Get the latest BMC analysis
            saved_analysis = await analysis_storage_service.get_user_analysis(
                user_id, idea_id, AnalysisType.BUSINESS_MODEL_CANVAS
            )
            
            if saved_analysis and saved_analysis.business_model_canvas_report:
                return saved_analysis.business_model_canvas_report
            
            return None
            
        except Exception as e:
            print(f"Error getting current BMC: {e}")
            return None
    
    async def _consolidate_insights(self, insights: List[ExtractedInsight]) -> Dict[str, Any]:
        """
        Consolidate and analyze patterns in insights
        """
        try:
            # Prepare insights data for analysis
            insights_data = []
            for insight in insights:
                insights_data.append({
                    "type": insight.type.value,
                    "content": insight.content,
                    "quote": insight.quote,
                    "confidence": insight.confidence.value,
                    "impact_score": insight.impact_score,
                    "tags": insight.tags
                })
            
            # Get consolidation analysis from AI
            formatted_prompt = self.insight_consolidation_prompt.format(
                insights=json.dumps(insights_data, indent=2)
            )
            
            response = await self.llm.ainvoke(formatted_prompt)
            
            try:
                consolidated = json.loads(response.content)
                return consolidated
            except json.JSONDecodeError:
                return {"patterns": [], "conflicts": [], "prioritized_insights": []}
                
        except Exception as e:
            print(f"Error consolidating insights: {e}")
            return {"patterns": [], "conflicts": [], "prioritized_insights": []}
    
    def _prepare_insight_summary(self, insights: List[ExtractedInsight]) -> Dict[str, Any]:
        """
        Prepare a summary of insights for AI analysis
        """
        summary = {
            "total_insights": len(insights),
            "by_type": {},
            "by_confidence": {},
            "high_impact_insights": [],
            "frequent_pain_points": [],
            "validation_signals": []
        }
        
        # Count by type
        for insight in insights:
            type_key = insight.type.value
            summary["by_type"][type_key] = summary["by_type"].get(type_key, 0) + 1
            
            confidence_key = insight.confidence.value
            summary["by_confidence"][confidence_key] = summary["by_confidence"].get(confidence_key, 0) + 1
            
            # Collect high impact insights
            if insight.impact_score >= 7.0:
                summary["high_impact_insights"].append({
                    "content": insight.content,
                    "quote": insight.quote,
                    "impact_score": insight.impact_score
                })
            
            # Collect pain points and validation signals
            if insight.type == InsightType.PAIN_POINT:
                summary["frequent_pain_points"].append(insight.content)
            elif insight.type == InsightType.VALIDATION_POINT:
                summary["validation_signals"].append(insight.content)
        
        return summary
    
    async def _get_bmc_update_recommendations(
        self,
        current_bmc: BusinessModelCanvas,
        insights: List[ExtractedInsight],
        insight_summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get AI recommendations for BMC updates
        """
        try:
            # Prepare data for AI analysis
            bmc_data = current_bmc.dict() if hasattr(current_bmc, 'dict') else current_bmc
            insights_data = [
                {
                    "type": insight.type.value,
                    "content": insight.content,
                    "quote": insight.quote,
                    "confidence": insight.confidence.value,
                    "impact_score": insight.impact_score
                }
                for insight in insights
            ]
            
            formatted_prompt = self.bmc_update_prompt.format(
                current_bmc=json.dumps(bmc_data, indent=2),
                insights=json.dumps(insights_data, indent=2),
                total_interviews=len(set(insight.interview_id for insight in insights)),
                confidence_summary=json.dumps(insight_summary.get("by_confidence", {})),
                frequent_pain_points=json.dumps(insight_summary.get("frequent_pain_points", [])),
                validation_signals=json.dumps(insight_summary.get("validation_signals", []))
            )
            
            response = await self.llm.ainvoke(formatted_prompt)
            
            try:
                recommendations = json.loads(response.content)
                return recommendations
            except json.JSONDecodeError:
                return self._create_fallback_recommendations()
                
        except Exception as e:
            print(f"Error getting BMC recommendations: {e}")
            return self._create_fallback_recommendations()
    
    async def _apply_updates_to_bmc(
        self,
        current_bmc: BusinessModelCanvas,
        recommendations: Dict[str, Any],
        insights: List[ExtractedInsight]
    ) -> BusinessModelCanvas:
        """
        Apply recommended updates to the BMC
        """
        try:
            # Start with current BMC data
            bmc_data = current_bmc.dict() if hasattr(current_bmc, 'dict') else current_bmc
            
            # Apply section updates
            section_updates = recommendations.get("section_updates", {})
            
            for section_name, update_data in section_updates.items():
                if section_name in bmc_data and update_data.get("confidence", 0) >= 7.0:
                    # Apply high-confidence updates
                    updates = update_data.get("updates", {})
                    
                    # Merge updates with existing data
                    if section_name in bmc_data:
                        section_data = bmc_data[section_name]
                        
                        # Update lists by extending rather than replacing
                        for key, value in updates.items():
                            if isinstance(value, list) and key in section_data:
                                if isinstance(section_data[key], list):
                                    # Add new items that don't already exist
                                    existing_items = set(section_data[key])
                                    new_items = [item for item in value if item not in existing_items]
                                    section_data[key].extend(new_items)
                                else:
                                    section_data[key] = value
                            else:
                                section_data[key] = value
            
            # Update metadata
            bmc_data["updated_at"] = datetime.utcnow()
            bmc_data["version"] = "updated_from_discovery"
            
            # Create updated BMC object
            # Note: You might need to adjust this based on your actual BMC model
            updated_bmc = BusinessModelCanvas(**bmc_data)
            
            return updated_bmc
            
        except Exception as e:
            print(f"Error applying BMC updates: {e}")
            return current_bmc
    
    async def _save_updated_bmc(
        self,
        user_id: str,
        idea_id: str,
        updated_bmc: BusinessModelCanvas,
        source_insights: List[ExtractedInsight]
    ) -> bool:
        """
        Save the updated BMC to the database
        """
        try:
            # Use the BMC workflow to save the updated canvas
            await simple_business_model_canvas_workflow._save_canvas_analysis(
                user_id, idea_id, updated_bmc
            )
            
            # Mark this as an update from customer discovery
            # You might want to add metadata about the source insights
            
            return True
            
        except Exception as e:
            print(f"Error saving updated BMC: {e}")
            return False
    
    async def _get_insights_by_interview_id(self, interview_id: str) -> List[ExtractedInsight]:
        """
        Get insights for a specific interview
        This is a placeholder - you'd implement this based on your storage system
        """
        # Placeholder implementation
        return []
    
    def _create_fallback_recommendations(self) -> Dict[str, Any]:
        """
        Create fallback recommendations when AI analysis fails
        """
        return {
            "update_summary": {
                "total_sections_updated": 0,
                "confidence_score": 0.0,
                "impact_level": "low",
                "recommendation": "No updates recommended due to analysis failure"
            },
            "section_updates": {},
            "new_insights": {
                "market_opportunities": [],
                "risks_identified": [],
                "assumptions_validated": [],
                "assumptions_invalidated": []
            },
            "next_steps": {
                "immediate_actions": ["Review insights manually"],
                "further_validation_needed": ["Verify insight quality"],
                "additional_interviews_suggested": []
            }
        }


# Create singleton instance
bmc_update_service = BMCUpdateService() 