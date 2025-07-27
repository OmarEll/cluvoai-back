import asyncio
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from langchain.prompts import ChatPromptTemplate

from core.business_model_models import (
    BusinessModelInput, RevenueModelRecommendation, RevenueModelType
)
from config.settings import settings


class RevenueModelRecommendationService:
    """
    Service for generating AI-powered revenue model recommendations
    using competitive intelligence and persona insights
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            openai_api_key=settings.openai_api_key,
            temperature=0.1
        )
        self.parser = JsonOutputParser()
        
        # Create the revenue model recommendation prompt
        self.revenue_model_prompt = ChatPromptTemplate.from_template("""
        You are an expert business model consultant. Analyze the business idea and recommend the best revenue models.
        
        Business Context:
        Business Idea: {business_idea}
        Target Market: {target_market}
        Industry: {industry}
        Estimated Users: {estimated_users}
        
        Competitive Intelligence:
        {competitive_context}
        
        Customer Persona Insights:
        {persona_context}
        
        Market Sizing Context:
        {market_sizing_context}
        
        Based on this comprehensive analysis, recommend the top 3 revenue models for this business.
        
        Consider:
        1. What revenue models are competitors using successfully?
        2. What are customers willing to pay for based on persona insights?
        3. What pricing strategies work in this market?
        4. Market size and customer behavior patterns
        5. Implementation complexity and time to revenue
        
        For each model, provide:
        - Model type (subscription, freemium, one_time_purchase, etc.)
        - Recommended price point based on competitive analysis
        - Price range (min/max) from competitive data
        - Pros and cons specific to this business
        - Suitability score (0-10) based on market fit
        - Real market examples from competitive research
        - Implementation complexity (Low/Medium/High)
        - Time to revenue (Immediate, 1-3 months, 3-6 months, 6+ months)
        
        Return as JSON array of revenue model recommendations.
        """)
    
    async def recommend_revenue_models(
        self,
        business_input: BusinessModelInput,
        competitive_context: Optional[Dict[str, Any]] = None,
        persona_context: Optional[Dict[str, Any]] = None,
        market_sizing_context: Optional[Dict[str, Any]] = None
    ) -> List[RevenueModelRecommendation]:
        """
        Generate revenue model recommendations using AI and context from other analyses
        """
        try:
            print("🎯 Generating revenue model recommendations with competitive intelligence...")
            
            # Format competitive context
            competitive_intel = self._format_competitive_context(competitive_context)
            
            # Format persona context
            persona_intel = self._format_persona_context(persona_context)
            
            # Format market sizing context
            market_intel = self._format_market_sizing_context(market_sizing_context)
            
            # Generate recommendations
            chain = self.revenue_model_prompt | self.llm | self.parser
            
            result = await asyncio.to_thread(
                chain.invoke,
                {
                    "business_idea": business_input.business_idea,
                    "target_market": business_input.target_market,
                    "industry": business_input.industry,
                    "estimated_users": business_input.estimated_users or "Not specified",
                    "competitive_context": competitive_intel,
                    "persona_context": persona_intel,
                    "market_sizing_context": market_intel
                }
            )
            
            # Parse and validate results
            recommendations = []
            if isinstance(result, list):
                for item in result:
                    try:
                        recommendation = self._parse_recommendation(item)
                        if recommendation:
                            recommendations.append(recommendation)
                    except Exception as e:
                        print(f"Error parsing recommendation: {e}")
                        continue
            
            # Ensure we have at least one recommendation
            if not recommendations:
                recommendations = await self._create_fallback_recommendations(business_input)
            
            # Sort by suitability score
            recommendations.sort(key=lambda x: x.suitability_score, reverse=True)
            
            print(f"✅ Generated {len(recommendations)} revenue model recommendations")
            return recommendations[:3]  # Return top 3
            
        except Exception as e:
            print(f"Error generating revenue model recommendations: {e}")
            return await self._create_fallback_recommendations(business_input)
    
    def _format_competitive_context(self, competitive_context: Optional[Dict[str, Any]]) -> str:
        """Format competitive intelligence for the prompt"""
        if not competitive_context:
            return "No competitive analysis data available."
        
        context_parts = []
        
        # Pricing intelligence
        if "pricing_intelligence" in competitive_context:
            pricing = competitive_context["pricing_intelligence"]
            if pricing.get("average_pricing", {}).get("price_range"):
                context_parts.append(f"Competitor pricing range: {pricing['average_pricing']['price_range']}")
            
            if pricing.get("pricing_models"):
                models = [p["model"] for p in pricing["pricing_models"]]
                context_parts.append(f"Common pricing models: {', '.join(set(models))}")
        
        # Market gaps and opportunities
        if "market_gaps" in competitive_context:
            gaps = [gap.get("description", str(gap)) for gap in competitive_context["market_gaps"]]
            context_parts.append(f"Market gaps: {'; '.join(gaps[:3])}")
        
        # Key insights
        if "key_insights" in competitive_context:
            insights = competitive_context["key_insights"][:2]
            context_parts.append(f"Key market insights: {'; '.join(insights)}")
        
        return "\n".join(context_parts) if context_parts else "Limited competitive data available."
    
    def _format_persona_context(self, persona_context: Optional[Dict[str, Any]]) -> str:
        """Format persona insights for the prompt"""
        if not persona_context:
            return "No persona analysis data available."
        
        context_parts = []
        
        if "personas" in persona_context:
            persona_count = len(persona_context["personas"])
            context_parts.append(f"Target personas identified: {persona_count}")
            
            # Extract key persona characteristics
            for i, persona in enumerate(persona_context["personas"][:2]):
                if isinstance(persona, dict):
                    persona_summary = f"Persona {i+1}: "
                    if "basic_info" in persona:
                        info = persona["basic_info"]
                        persona_summary += f"{info.get('name', 'Unknown')} - {info.get('title', 'Professional')}"
                    
                    if "demographics" in persona:
                        demo = persona["demographics"]
                        if demo.get("income_range"):
                            persona_summary += f", Income: {demo['income_range']}"
                    
                    context_parts.append(persona_summary)
        
        return "\n".join(context_parts) if context_parts else "Limited persona data available."
    
    def _format_market_sizing_context(self, market_sizing_context: Optional[Dict[str, Any]]) -> str:
        """Format market sizing insights for the prompt"""
        if not market_sizing_context:
            return "No market sizing data available."
        
        context_parts = []
        
        if "tam_sam_som_breakdown" in market_sizing_context:
            breakdown = market_sizing_context["tam_sam_som_breakdown"]
            tam = breakdown.get("tam", 0)
            sam = breakdown.get("sam", 0)
            som = breakdown.get("som", 0)
            context_parts.append(f"Market size - TAM: ${tam:,.0f}, SAM: ${sam:,.0f}, SOM: ${som:,.0f}")
        
        if "competitive_position" in market_sizing_context:
            position = market_sizing_context["competitive_position"]
            if position.get("market_gaps"):
                gaps = len(position["market_gaps"])
                context_parts.append(f"Market opportunities identified: {gaps}")
        
        return "\n".join(context_parts) if context_parts else "Limited market sizing data available."
    
    def _parse_recommendation(self, item: Dict[str, Any]) -> Optional[RevenueModelRecommendation]:
        """Parse a single recommendation from AI response"""
        try:
            # Map model type string to enum
            model_type_str = item.get("model_type", "subscription").lower()
            model_type = self._map_to_revenue_model_type(model_type_str)
            
            return RevenueModelRecommendation(
                model_type=model_type,
                recommended_price=item.get("recommended_price"),
                price_range=item.get("price_range", {}),
                pros=item.get("pros", []),
                cons=item.get("cons", []),
                suitability_score=float(item.get("suitability_score", 5.0)),
                market_examples=item.get("market_examples", []),
                implementation_complexity=item.get("implementation_complexity", "Medium"),
                time_to_revenue=item.get("time_to_revenue", "3-6 months")
            )
        except Exception as e:
            print(f"Error parsing recommendation item: {e}")
            return None
    
    def _map_to_revenue_model_type(self, model_type_str: str) -> RevenueModelType:
        """Map string to RevenueModelType enum"""
        mapping = {
            "subscription": RevenueModelType.SUBSCRIPTION,
            "freemium": RevenueModelType.FREEMIUM,
            "premium": RevenueModelType.PREMIUM,
            "one_time": RevenueModelType.ONE_TIME,
            "one_time_purchase": RevenueModelType.ONE_TIME,
            "marketplace": RevenueModelType.MARKETPLACE,
            "marketplace_commission": RevenueModelType.MARKETPLACE,
            "sponsorship": RevenueModelType.SPONSORSHIP,
            "advertising": RevenueModelType.ADVERTISING,
            "transaction_fee": RevenueModelType.TRANSACTION_FEE,
            "licensing": RevenueModelType.LICENSING,
            "consulting": RevenueModelType.CONSULTING
        }
        
        return mapping.get(model_type_str, RevenueModelType.SUBSCRIPTION)
    
    async def _create_fallback_recommendations(self, business_input: BusinessModelInput) -> List[RevenueModelRecommendation]:
        """Create fallback recommendations when AI generation fails"""
        return [
            RevenueModelRecommendation(
                model_type=RevenueModelType.SUBSCRIPTION,
                recommended_price=29.99,
                price_range={"min": 9.99, "max": 99.99},
                pros=["Predictable recurring revenue", "Customer lifetime value", "Scalable growth"],
                cons=["Customer acquisition cost", "Churn management", "Feature development pressure"],
                suitability_score=7.5,
                market_examples=["Similar SaaS businesses"],
                implementation_complexity="Medium",
                time_to_revenue="1-3 months"
            ),
            RevenueModelRecommendation(
                model_type=RevenueModelType.FREEMIUM,
                recommended_price=0.0,
                price_range={"min": 0.0, "max": 49.99},
                pros=["Low barrier to entry", "Viral growth potential", "Market penetration"],
                cons=["Complex conversion funnel", "High support costs", "Feature differentiation"],
                suitability_score=6.0,
                market_examples=["Freemium software platforms"],
                implementation_complexity="High",
                time_to_revenue="3-6 months"
            ),
            RevenueModelRecommendation(
                model_type=RevenueModelType.ONE_TIME,
                recommended_price=199.99,
                price_range={"min": 99.99, "max": 499.99},
                pros=["Immediate revenue", "Simple pricing", "Lower churn concern"],
                cons=["No recurring revenue", "Customer re-engagement", "Growth limitations"],
                suitability_score=5.5,
                market_examples=["Software licenses and tools"],
                implementation_complexity="Low",
                time_to_revenue="Immediate"
            )
        ]


# Create singleton instance
revenue_model_service = RevenueModelRecommendationService() 