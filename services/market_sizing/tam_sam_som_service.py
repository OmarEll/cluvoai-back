import asyncio
from typing import Dict, List, Optional, Any, Tuple
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from core.market_models import (
    TAMSAMSOMBreakdown, MarketSizingInput, MarketData, 
    GeographicScope, CustomerType, RevenueModel
)
from config.settings import settings


class TAMSAMSOMCalculationService:
    """Service for calculating Total Addressable Market, Serviceable Addressable Market, and Serviceable Obtainable Market"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model_name="gpt-4",
            temperature=0.2,  # Lower temperature for more consistent calculations
            openai_api_key=settings.openai_api_key
        )
        
        # Prompt for TAM/SAM/SOM calculations
        self.tam_sam_som_prompt = ChatPromptTemplate.from_template("""
        You are a professional market analyst specializing in TAM/SAM/SOM calculations for startup valuation and market analysis.
        
        Calculate TAM, SAM, and SOM for the following business:
        
        Business Idea: {business_idea}
        Industry: {industry}
        Target Market: {target_market}
        Geographic Scope: {geographic_scope}
        Customer Type: {customer_type}
        Revenue Model: {revenue_model}
        Estimated Price Point: ${price_point}
        
        Market Data Context:
        - Current Market Size: ${current_market_size:,.0f}
        - Market Growth Rate: {growth_rate}%
        - Industry Overview: {industry_overview}
        
        Additional Context: {additional_context}
        
        Competitive Intelligence Available:
        {competitive_intelligence}
        
        Provide detailed TAM/SAM/SOM calculations with clear methodology:
        
        TAM (Total Addressable Market):
        - The entire market demand for the product/service category globally or in specified region
        - Include ALL potential customers who could theoretically use this solution
        - Use top-down approach (market size data) and bottom-up approach (customer segments × price)
        
        SAM (Serviceable Addressable Market):
        - The segment of TAM that your business model can realistically serve
        - Consider geographic constraints, regulatory limitations, business model constraints
        - Factor in competition and market maturity
        
        SOM (Serviceable Obtainable Market):
        - The portion of SAM you can realistically capture in the next 3-5 years
        - Consider competitive landscape, resources, market penetration rates
        - Use realistic market share assumptions based on similar companies
        
        Return as JSON:
        {{
            "tam": {{
                "value": <number_in_usd>,
                "methodology": "<detailed_explanation>",
                "calculation_approach": "<top_down_or_bottom_up_or_both>",
                "key_assumptions": ["<assumption1>", "<assumption2>"]
            }},
            "sam": {{
                "value": <number_in_usd>,
                "percentage_of_tam": <percentage>,
                "methodology": "<detailed_explanation>",
                "limiting_factors": ["<factor1>", "<factor2>"],
                "addressable_segments": ["<segment1>", "<segment2>"]
            }},
            "som": {{
                "value": <number_in_usd>,
                "percentage_of_sam": <percentage>,
                "percentage_of_tam": <percentage>,
                "methodology": "<detailed_explanation>",
                "market_penetration_assumptions": "<realistic_penetration_rate>",
                "competitive_factors": ["<factor1>", "<factor2>"],
                "timeframe": "3-5 years"
            }},
            "market_penetration_rate": <expected_percentage>,
            "validation_checks": {{
                "tam_reasonableness": "<assessment>",
                "sam_constraints": "<assessment>",
                "som_achievability": "<assessment>"
            }}
        }}
        """)
    
    async def calculate_tam_sam_som(
        self,
        analysis_input: MarketSizingInput,
        market_data: MarketData,
        competitor_context: Optional[Dict[str, Any]] = None,
        persona_context: Optional[Dict[str, Any]] = None
    ) -> TAMSAMSOMBreakdown:
        """
        Calculate TAM, SAM, and SOM using AI-powered analysis with market data
        """
        try:
            print("📊 Calculating TAM/SAM/SOM breakdown...")
            
            # Prepare additional context from competitor and persona analysis
            additional_context = self._prepare_additional_context(competitor_context, persona_context)
            
            # Prepare competitive intelligence context
            competitive_intelligence = self._format_competitive_intelligence(competitor_context)
            
            # Generate TAM/SAM/SOM calculations
            calculations = await self._generate_tam_sam_som_calculations(
                analysis_input, market_data, additional_context, competitive_intelligence
            )
            
            # Validate and refine calculations
            validated_calculations = await self._validate_calculations(calculations, market_data)
            
            # Create TAM/SAM/SOM breakdown
            breakdown = self._create_breakdown(validated_calculations)
            
            print(f"✅ TAM/SAM/SOM calculated - TAM: ${breakdown.tam:,.0f}, SAM: ${breakdown.sam:,.0f}, SOM: ${breakdown.som:,.0f}")
            return breakdown
            
        except Exception as e:
            print(f"Error calculating TAM/SAM/SOM: {e}")
            return await self._create_fallback_breakdown(analysis_input, market_data)
    
    async def _generate_tam_sam_som_calculations(
        self,
        analysis_input: MarketSizingInput,
        market_data: MarketData,
        additional_context: str,
        competitive_intelligence: str = ""
    ) -> Dict[str, Any]:
        """Generate TAM/SAM/SOM calculations using AI"""
        try:
            chain = self.tam_sam_som_prompt | self.llm | JsonOutputParser()
            
            result = await asyncio.to_thread(
                chain.invoke,
                {
                    "business_idea": analysis_input.business_idea,
                    "industry": analysis_input.industry,
                    "target_market": analysis_input.target_market,
                    "geographic_scope": analysis_input.geographic_scope.value.replace('_', ' '),
                    "customer_type": analysis_input.customer_type.value,
                    "revenue_model": analysis_input.revenue_model.value,
                    "price_point": analysis_input.estimated_price_point or 100,
                    "current_market_size": market_data.market_size_current,
                    "growth_rate": market_data.market_growth_rate,
                    "industry_overview": market_data.industry_overview,
                    "additional_context": additional_context,
                    "competitive_intelligence": competitive_intelligence
                }
            )
            
            return result if isinstance(result, dict) else {}
            
        except Exception as e:
            print(f"Error generating TAM/SAM/SOM calculations: {e}")
            return {}
    
    def _prepare_additional_context(
        self,
        competitor_context: Optional[Dict[str, Any]],
        persona_context: Optional[Dict[str, Any]]
    ) -> str:
        """Prepare additional context from competitor and persona analysis"""
        context_parts = []
        
        if competitor_context:
            # Extract relevant competitor insights
            if "market_gaps" in competitor_context:
                context_parts.append(f"Market gaps identified: {', '.join(competitor_context['market_gaps'])}")
            
            if "competitive_advantages" in competitor_context:
                context_parts.append(f"Potential competitive advantages: {', '.join(competitor_context['competitive_advantages'])}")
            
            if "pricing_insights" in competitor_context:
                pricing = competitor_context["pricing_insights"]
                if pricing:
                    context_parts.append(f"Competitor pricing insights available from {len(pricing)} competitors")
        
        if persona_context:
            # Extract relevant persona insights
            if "target_segments" in persona_context:
                context_parts.append(f"Target customer segments identified: {len(persona_context['target_segments'])} segments")
            
            if "market_size_validation" in persona_context:
                context_parts.append(f"Persona-based market validation: {persona_context['market_size_validation']}")
        
        return ". ".join(context_parts) if context_parts else "No additional context available."
    
    async def _validate_calculations(
        self,
        calculations: Dict[str, Any],
        market_data: MarketData
    ) -> Dict[str, Any]:
        """Validate and refine TAM/SAM/SOM calculations"""
        
        if not calculations:
            return await self._create_fallback_calculations(market_data)
        
        try:
            # Extract values with validation
            tam_data = calculations.get("tam", {})
            sam_data = calculations.get("sam", {})
            som_data = calculations.get("som", {})
            
            # Validate TAM
            tam_value = float(tam_data.get("value", 0))
            if tam_value <= 0 or tam_value > market_data.market_size_current * 5:  # TAM shouldn't be >5x total market
                tam_value = market_data.market_size_current * 1.2  # Reasonable default
            
            # Validate SAM (should be <= TAM)
            sam_value = float(sam_data.get("value", 0))
            if sam_value <= 0 or sam_value > tam_value:
                sam_value = tam_value * 0.3  # 30% of TAM default
            
            # Validate SOM (should be <= SAM)
            som_value = float(som_data.get("value", 0))
            if som_value <= 0 or som_value > sam_value:
                som_value = sam_value * 0.1  # 10% of SAM default
            
            # Update calculations with validated values
            calculations["tam"]["value"] = tam_value
            calculations["sam"]["value"] = sam_value
            calculations["sam"]["percentage_of_tam"] = (sam_value / tam_value) * 100
            calculations["som"]["value"] = som_value
            calculations["som"]["percentage_of_sam"] = (som_value / sam_value) * 100
            calculations["som"]["percentage_of_tam"] = (som_value / tam_value) * 100
            
            # Calculate realistic market penetration rate
            penetration_rate = (som_value / sam_value) * 100
            calculations["market_penetration_rate"] = min(penetration_rate, 15.0)  # Cap at 15%
            
            return calculations
            
        except Exception as e:
            print(f"Error validating calculations: {e}")
            return await self._create_fallback_calculations(market_data)
    
    def _create_breakdown(self, calculations: Dict[str, Any]) -> TAMSAMSOMBreakdown:
        """Create TAMSAMSOMBreakdown from calculations"""
        
        tam_data = calculations.get("tam", {})
        sam_data = calculations.get("sam", {})
        som_data = calculations.get("som", {})
        
        return TAMSAMSOMBreakdown(
            tam=tam_data.get("value", 0),
            tam_description=tam_data.get("methodology", "Total addressable market calculation"),
            sam=sam_data.get("value", 0),
            sam_description=sam_data.get("methodology", "Serviceable addressable market calculation"),
            som=som_data.get("value", 0),
            som_description=som_data.get("methodology", "Serviceable obtainable market calculation"),
            market_penetration_rate=calculations.get("market_penetration_rate", 5.0)
        )
    
    async def _create_fallback_calculations(self, market_data: MarketData) -> Dict[str, Any]:
        """Create fallback calculations when AI generation fails"""
        
        # Use rule-based fallback calculations
        tam_value = market_data.market_size_current * 1.1  # Slightly larger than current market
        sam_value = tam_value * 0.25  # 25% of TAM
        som_value = sam_value * 0.08  # 8% of SAM (2% of TAM)
        
        return {
            "tam": {
                "value": tam_value,
                "methodology": "Fallback calculation based on current market size with growth assumptions",
                "calculation_approach": "Top-down approach using market data",
                "key_assumptions": ["Market continues current growth trajectory", "Geographic expansion possible"]
            },
            "sam": {
                "value": sam_value,
                "percentage_of_tam": 25.0,
                "methodology": "Conservative estimate of serviceable market based on business model constraints",
                "limiting_factors": ["Geographic limitations", "Business model constraints", "Regulatory requirements"],
                "addressable_segments": ["Primary target segment"]
            },
            "som": {
                "value": som_value,
                "percentage_of_sam": 8.0,
                "percentage_of_tam": 2.0,
                "methodology": "Realistic market capture based on typical startup penetration rates",
                "market_penetration_assumptions": "Conservative 2% market penetration over 5 years",
                "competitive_factors": ["Established competition", "Customer acquisition challenges"],
                "timeframe": "3-5 years"
            },
            "market_penetration_rate": 8.0
        }
    
    async def _create_fallback_breakdown(
        self,
        analysis_input: MarketSizingInput,
        market_data: MarketData
    ) -> TAMSAMSOMBreakdown:
        """Create fallback TAM/SAM/SOM breakdown"""
        
        calculations = await self._create_fallback_calculations(market_data)
        return self._create_breakdown(calculations)

    def _format_competitive_intelligence(self, competitor_context: Optional[Dict[str, Any]]) -> str:
        """Format competitive intelligence for use in prompts"""
        if not competitor_context:
            return "No competitive analysis data available."
        
        intelligence_parts = []
        
        # Market size indicators
        if "market_size_indicators" in competitor_context:
            indicators = competitor_context["market_size_indicators"]
            intelligence_parts.append("MARKET SIZE INDICATORS:")
            
            if indicators.get("funding_insights", {}).get("average_funding"):
                avg_funding = indicators["funding_insights"]["average_funding"]
                intelligence_parts.append(f"- Average competitor funding: ${avg_funding:,.0f}")
            
            if indicators.get("market_validation", {}).get("total_employees"):
                total_employees = indicators["market_validation"]["total_employees"]
                intelligence_parts.append(f"- Total employees across competitors: {total_employees:,}")
            
            maturity_score = indicators.get("funding_insights", {}).get("market_maturity_score", 0)
            intelligence_parts.append(f"- Market maturity score: {maturity_score:.1f}/10")
        
        # Pricing intelligence
        if "pricing_intelligence" in competitor_context:
            pricing = competitor_context["pricing_intelligence"]
            intelligence_parts.append("\nPRICING INTELLIGENCE:")
            
            if pricing.get("average_pricing", {}).get("price_range"):
                intelligence_parts.append(f"- Competitor price range: {pricing['average_pricing']['price_range']}")
            
            freemium_count = pricing.get("price_ranges", {}).get("freemium_available", 0)
            if freemium_count > 0:
                intelligence_parts.append(f"- {freemium_count} competitors offer freemium models")
        
        # Competitive landscape
        if "competitive_landscape" in competitor_context:
            landscape = competitor_context["competitive_landscape"]
            intelligence_parts.append("\nCOMPETITIVE LANDSCAPE:")
            
            concentration = landscape.get("market_concentration", "unknown")
            intelligence_parts.append(f"- Market concentration: {concentration}")
            
            if landscape.get("market_leaders"):
                leader_count = len(landscape["market_leaders"])
                intelligence_parts.append(f"- Identified {leader_count} market leaders")
            
            if landscape.get("barriers_to_entry"):
                barriers = [b["type"] for b in landscape["barriers_to_entry"]]
                intelligence_parts.append(f"- Key barriers to entry: {', '.join(barriers)}")
        
        # Market sentiment insights
        if "market_sentiment_insights" in competitor_context:
            sentiment = competitor_context["market_sentiment_insights"]
            intelligence_parts.append("\nMARKET SENTIMENT:")
            
            satisfaction = sentiment.get("market_satisfaction_level", "unknown")
            intelligence_parts.append(f"- Overall market satisfaction: {satisfaction}")
            
            if sentiment.get("common_user_complaints"):
                top_complaints = [c["complaint"] for c in sentiment["common_user_complaints"][:2]]
                intelligence_parts.append(f"- Top user complaints: {'; '.join(top_complaints)}")
        
        # SWOT insights
        if "swot_insights" in competitor_context:
            swot = competitor_context["swot_insights"]
            intelligence_parts.append("\nMARKET POSITIONING OPPORTUNITIES:")
            
            if swot.get("positioning_gaps"):
                gaps = swot["positioning_gaps"][:3]
                intelligence_parts.append(f"- Key positioning gaps: {'; '.join(gaps)}")
            
            if swot.get("market_weaknesses"):
                weakness_themes = [w["theme"] for w in swot["market_weaknesses"][:2]]
                intelligence_parts.append(f"- Market weakness areas: {', '.join(weakness_themes)}")
        
        return "\n".join(intelligence_parts) if intelligence_parts else "Limited competitive intelligence available."


# Create singleton instance
tam_sam_som_service = TAMSAMSOMCalculationService() 