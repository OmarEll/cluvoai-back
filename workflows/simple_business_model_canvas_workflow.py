import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from core.business_model_canvas_models import BusinessModelCanvas
from services.business_model_canvas.canvas_generator_service import canvas_generator_service
from services.feature_orchestration_service import feature_orchestration_service
from services.analysis_storage_service import analysis_storage_service
from core.analysis_models import AnalysisType


class SimpleBusinessModelCanvasWorkflow:
    """
    Simple sequential workflow for Business Model Canvas generation
    that leverages competitive analysis, persona insights, market sizing, and business model data
    """
    
    def __init__(self):
        self.canvas_generator = canvas_generator_service
        self.feature_orchestration = feature_orchestration_service
        self.analysis_storage = analysis_storage_service
    
    async def run_canvas_analysis(
        self,
        business_idea: str,
        target_market: str,
        industry: str,
        user_id: Optional[str] = None,
        idea_id: Optional[str] = None
    ) -> BusinessModelCanvas:
        """
        Run complete Business Model Canvas analysis with cross-feature context
        """
        try:
            print("🎨 Starting Business Model Canvas analysis with cross-feature context...")
            start_time = datetime.utcnow()
            
            # Step 1: Collect existing analysis context
            competitive_context = None
            persona_context = None
            market_sizing_context = None
            business_model_context = None
            
            if user_id and idea_id:
                print("🔍 Collecting existing analysis context for enhanced canvas...")
                context = await self._collect_existing_context(user_id, idea_id)
                competitive_context = context.get("competitive")
                persona_context = context.get("persona")
                market_sizing_context = context.get("market_sizing")
                business_model_context = context.get("business_model")
                
                if competitive_context:
                    print(f"✅ Found competitive analysis with {competitive_context.get('total_competitors', 0)} competitors")
                if persona_context:
                    print(f"✅ Found persona analysis with {persona_context.get('personas_analyzed', 0)} personas")
                if market_sizing_context:
                    print(f"✅ Found market sizing analysis")
                if business_model_context:
                    print(f"✅ Found business model analysis")
            
            # Step 2: Generate comprehensive canvas
            print("📊 Generating comprehensive Business Model Canvas...")
            start_time = datetime.utcnow()
            
            try:
                canvas = await self.canvas_generator.generate_comprehensive_canvas(
                    business_idea=business_idea,
                    target_market=target_market,
                    industry=industry,
                    competitive_context=competitive_context,
                    persona_context=persona_context,
                    market_sizing_context=market_sizing_context,
                    business_model_context=business_model_context
                )
                
                # Check if the canvas has sufficient data, if not use enhanced fallback
                if not self._has_sufficient_data(canvas):
                    print("⚠️ AI-generated canvas lacks sufficient data, using enhanced fallback...")
                    canvas = await self.canvas_generator._create_fallback_canvas(
                        business_idea, target_market, industry
                    )
                
            except Exception as e:
                print(f"⚠️ AI generation failed, using enhanced fallback canvas: {e}")
                canvas = await self.canvas_generator._create_fallback_canvas(
                    business_idea, target_market, industry
                )
            
            # Step 3: Save analysis if user is authenticated
            if user_id and idea_id:
                print("💾 Saving Business Model Canvas analysis...")
                await self._save_canvas_analysis(user_id, idea_id, canvas)
                
                # Mark analysis as completed
                await self.feature_orchestration.mark_analysis_completed(
                    user_id, idea_id, AnalysisType.BUSINESS_MODEL_CANVAS
                )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            print(f"✅ Business Model Canvas analysis completed successfully in {execution_time:.2f} seconds")
            
            return canvas
            
        except Exception as e:
            print(f"Error in Business Model Canvas workflow: {e}")
            # Return fallback canvas
            return await self.canvas_generator._create_fallback_canvas(business_idea, target_market, industry)
    
    async def _collect_existing_context(self, user_id: str, idea_id: str) -> Dict[str, Any]:
        """Collect context from all previous analyses"""
        context = {}
        
        try:
            # Get competitive analysis context
            competitive_analysis = await self.analysis_storage.get_user_analysis(
                user_id, idea_id, AnalysisType.COMPETITOR
            )
            if competitive_analysis and competitive_analysis.competitor_report:
                context["competitive"] = self._extract_competitive_context(competitive_analysis.competitor_report)
            
            # Get persona analysis context
            persona_analysis = await self.analysis_storage.get_user_analysis(
                user_id, idea_id, AnalysisType.PERSONA
            )
            if persona_analysis and persona_analysis.persona_report:
                context["persona"] = self._extract_persona_context(persona_analysis.persona_report)
            
            # Get market sizing context
            market_sizing_analysis = await self.analysis_storage.get_user_analysis(
                user_id, idea_id, AnalysisType.MARKET_SIZING
            )
            if market_sizing_analysis and market_sizing_analysis.market_sizing_report:
                context["market_sizing"] = self._extract_market_sizing_context(market_sizing_analysis.market_sizing_report)
            
            # Get business model context
            business_model_analysis = await self.analysis_storage.get_user_analysis(
                user_id, idea_id, AnalysisType.BUSINESS_MODEL
            )
            if business_model_analysis and business_model_analysis.business_model_report:
                context["business_model"] = self._extract_business_model_context(business_model_analysis.business_model_report)
            
        except Exception as e:
            print(f"Warning: Error collecting existing context: {e}")
        
        return context
    
    def _extract_competitive_context(self, competitor_report: Any) -> Dict[str, Any]:
        """Extract competitive intelligence for canvas context"""
        try:
            context = {
                "total_competitors": len(competitor_report.competitors) if hasattr(competitor_report, 'competitors') else 0,
                "market_gaps": competitor_report.market_gaps if hasattr(competitor_report, 'market_gaps') else [],
                "key_insights": []
            }
            
            # Extract key insights from competitors
            if hasattr(competitor_report, 'competitors'):
                for competitor in competitor_report.competitors[:3]:  # Top 3 competitors
                    if hasattr(competitor, 'swot_analysis'):
                        swot = competitor.swot_analysis
                        if hasattr(swot, 'strengths') and swot.strengths:
                            context["key_insights"].append(f"{competitor.name}: {swot.strengths[0]}")
            
            return context
        except Exception as e:
            print(f"Error extracting competitive context: {e}")
            return {"total_competitors": 0, "market_gaps": [], "key_insights": []}
    
    def _extract_persona_context(self, persona_report: Any) -> Dict[str, Any]:
        """Extract persona insights for canvas context"""
        try:
            context = {
                "personas_analyzed": len(persona_report.personas) if hasattr(persona_report, 'personas') else 0,
                "pricing_sensitivity": {
                    "high_sensitivity_count": 0,
                    "low_sensitivity_count": 0
                }
            }
            
            # Analyze pricing sensitivity from personas
            if hasattr(persona_report, 'personas'):
                for persona in persona_report.personas:
                    if hasattr(persona, 'pricing_sensitivity'):
                        if persona.pricing_sensitivity == "high":
                            context["pricing_sensitivity"]["high_sensitivity_count"] += 1
                        else:
                            context["pricing_sensitivity"]["low_sensitivity_count"] += 1
            
            return context
        except Exception as e:
            print(f"Error extracting persona context: {e}")
            return {"personas_analyzed": 0, "pricing_sensitivity": {"high_sensitivity_count": 0, "low_sensitivity_count": 0}}
    
    def _extract_market_sizing_context(self, market_sizing_report: Any) -> Dict[str, Any]:
        """Extract market sizing data for canvas context"""
        try:
            context = {
                "market_size": {},
                "revenue_opportunity": {}
            }
            
            if hasattr(market_sizing_report, 'tam_sam_som_breakdown'):
                breakdown = market_sizing_report.tam_sam_som_breakdown
                context["market_size"] = {
                    "tam": breakdown.tam if hasattr(breakdown, 'tam') else 0,
                    "sam": breakdown.sam if hasattr(breakdown, 'sam') else 0,
                    "som": breakdown.som if hasattr(breakdown, 'som') else 0
                }
            
            if hasattr(market_sizing_report, 'revenue_projections'):
                projections = market_sizing_report.revenue_projections
                if projections and len(projections) > 0:
                    context["revenue_opportunity"] = {
                        "obtainable_market": projections[0].projected_revenue if hasattr(projections[0], 'projected_revenue') else 0
                    }
            
            return context
        except Exception as e:
            print(f"Error extracting market sizing context: {e}")
            return {"market_size": {}, "revenue_opportunity": {}}
    
    def _extract_business_model_context(self, business_model_report: Any) -> Dict[str, Any]:
        """Extract business model insights for canvas context"""
        try:
            context = {
                "primary_recommendation": {},
                "profitability_projections": []
            }
            
            if hasattr(business_model_report, 'primary_recommendation'):
                context["primary_recommendation"] = {
                    "model_type": business_model_report.primary_recommendation.model_type if hasattr(business_model_report.primary_recommendation, 'model_type') else "N/A",
                    "recommended_price": business_model_report.primary_recommendation.recommended_price if hasattr(business_model_report.primary_recommendation, 'recommended_price') else "N/A"
                }
            
            if hasattr(business_model_report, 'profitability_projections'):
                projections = business_model_report.profitability_projections
                for proj in projections[:2]:  # First 2 projections
                    context["profitability_projections"].append({
                        "monthly_revenue": proj.monthly_revenue if hasattr(proj, 'monthly_revenue') else 0,
                        "break_even_months": proj.break_even_months if hasattr(proj, 'break_even_months') else 0
                    })
            
            return context
        except Exception as e:
            print(f"Error extracting business model context: {e}")
            return {"primary_recommendation": {}, "profitability_projections": []}
    
    async def _save_canvas_analysis(self, user_id: str, idea_id: str, canvas: BusinessModelCanvas) -> None:
        """Save canvas analysis to database"""
        try:
            await self.analysis_storage.save_analysis_result(
                user_id=user_id,
                idea_id=idea_id,
                analysis_type=AnalysisType.BUSINESS_MODEL_CANVAS,
                business_model_canvas_report=canvas
            )
            print("✅ Business Model Canvas analysis saved successfully")
        except Exception as e:
            print(f"Error saving canvas analysis: {e}")

    def _has_sufficient_data(self, canvas: BusinessModelCanvas) -> bool:
        """
        Check if the generated canvas has sufficient data for a complete analysis.
        """
        try:
            # Check if customer segments have meaningful data
            customer_segments = canvas.customer_segments
            if not customer_segments or len(customer_segments.characteristics or []) < 3:
                return False
            
            # Check if value propositions have meaningful data
            value_propositions = canvas.value_propositions
            if not value_propositions or len(value_propositions.benefits or []) < 3:
                return False
            
            # Check if channels have meaningful data
            channels = canvas.channels
            if not channels or len(channels.touchpoints or []) < 2:
                return False
            
            # Check if revenue streams have meaningful data
            revenue_streams = canvas.revenue_streams
            if not revenue_streams or not revenue_streams.pricing_model:
                return False
            
            # Check if key resources have meaningful data
            key_resources = canvas.key_resources
            if not key_resources or not key_resources.description:
                return False
            
            # Check if key activities have meaningful data
            key_activities = canvas.key_activities
            if not key_activities or not key_activities.description:
                return False
            
            # Check if key partnerships have meaningful data
            key_partnerships = canvas.key_partnerships
            if not key_partnerships or len(key_partnerships.partner_categories or []) < 2:
                return False
            
            # Check if cost structure has meaningful data
            cost_structure = canvas.cost_structure
            if not cost_structure or len(cost_structure.fixed_costs or []) < 2:
                return False
            
            return True
            
        except Exception as e:
            print(f"Error checking data sufficiency: {e}")
            return False


# Create singleton instance
simple_business_model_canvas_workflow = SimpleBusinessModelCanvasWorkflow() 