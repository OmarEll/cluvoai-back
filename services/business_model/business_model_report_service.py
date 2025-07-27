import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from langchain.prompts import ChatPromptTemplate

from core.business_model_models import (
    BusinessModelInput, BusinessModelReport, RevenueModelRecommendation,
    ProfitabilityProjection, PricingInsights, MarketBenchmarks, PricingStrategy
)
from services.business_model.revenue_model_service import revenue_model_service
from services.business_model.profitability_service import profitability_service
from config.settings import settings


class BusinessModelReportService:
    """
    Service for generating comprehensive business model reports
    that leverage competitive analysis, persona insights, and market sizing data
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            openai_api_key=settings.openai_api_key,
            temperature=0.1
        )
        self.parser = JsonOutputParser()
        
        # Pricing insights prompt
        self.pricing_prompt = ChatPromptTemplate.from_template("""
        You are a pricing strategy expert. Analyze the business and market data to recommend optimal pricing strategies.
        
        Business Context:
        Business Idea: {business_idea}
        Industry: {industry}
        Target Market: {target_market}
        
        Competitive Intelligence:
        {competitive_context}
        
        Customer Personas:
        {persona_context}
        
        Market Sizing:
        {market_sizing_context}
        
        Recommended Revenue Model: {revenue_model}
        Current Price Point: ${price_point}
        
        Based on this comprehensive analysis, provide pricing strategy insights:
        
        1. Recommended pricing strategy (penetration, premium, competitive, value_based, freemium, tiered)
        2. Competitive price range analysis
        3. Suggested pricing tiers with features and prices
        4. Price elasticity insights based on persona analysis
        5. Optimization recommendations
        
        Consider:
        - What competitors are charging and their value propositions
        - Customer personas' willingness to pay and price sensitivity
        - Market positioning from competitive analysis
        - Value perception from persona insights
        
        Return as JSON with pricing strategy insights.
        """)
        
        # Market benchmarks prompt
        self.benchmarks_prompt = ChatPromptTemplate.from_template("""
        You are a market research analyst. Provide industry benchmarks and metrics for this business model.
        
        Business Context:
        Business Idea: {business_idea}
        Industry: {industry}
        Revenue Model: {revenue_model}
        
        Market Intelligence:
        {market_intelligence}
        
        Provide realistic industry benchmarks including:
        1. Customer Acquisition Cost (CAC) for this industry and model
        2. Customer Lifetime Value (LTV) estimates
        3. LTV:CAC ratio expectations
        4. Monthly churn rate benchmarks
        5. Average Revenue Per User (ARPU)
        6. Market growth rate
        7. Competitive landscape summary
        
        Base estimates on industry standards and market data provided.
        Return as JSON with benchmark metrics.
        """)
    
    async def generate_comprehensive_report(
        self,
        business_input: BusinessModelInput,
        competitive_context: Optional[Dict[str, Any]] = None,
        persona_context: Optional[Dict[str, Any]] = None,
        market_sizing_context: Optional[Dict[str, Any]] = None
    ) -> BusinessModelReport:
        """
        Generate a comprehensive business model report using all available context
        """
        try:
            print("📊 Generating comprehensive business model report...")
            start_time = datetime.utcnow()
            
            # Step 1: Generate revenue model recommendations
            print("🎯 Analyzing revenue models with competitive intelligence...")
            revenue_recommendations = await revenue_model_service.recommend_revenue_models(
                business_input, competitive_context, persona_context, market_sizing_context
            )
            
            # Select primary recommendation (highest scoring)
            primary_recommendation = revenue_recommendations[0] if revenue_recommendations else self._create_default_recommendation()
            
            # Step 2: Generate profitability projections
            print("💰 Calculating profitability scenarios...")
            market_intelligence = self._combine_market_intelligence(
                competitive_context, persona_context, market_sizing_context
            )
            
            profitability_projections = await profitability_service.calculate_profitability_projections(
                business_input, primary_recommendation, market_intelligence
            )
            
            # Step 3: Generate pricing insights
            print("💲 Analyzing pricing strategies...")
            pricing_insights = await self._generate_pricing_insights(
                business_input, primary_recommendation, competitive_context, 
                persona_context, market_sizing_context
            )
            
            # Step 4: Generate market benchmarks
            print("📈 Calculating market benchmarks...")
            market_benchmarks = await self._generate_market_benchmarks(
                business_input, primary_recommendation, market_intelligence
            )
            
            # Step 5: Generate implementation guidance
            print("🗺️ Creating implementation roadmap...")
            implementation_roadmap = self._generate_implementation_roadmap(
                primary_recommendation, competitive_context
            )
            
            risk_factors = self._generate_risk_factors(
                primary_recommendation, competitive_context, market_sizing_context
            )
            
            success_metrics = self._generate_success_metrics(
                primary_recommendation, market_benchmarks
            )
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Create comprehensive report
            report = BusinessModelReport(
                business_idea=business_input.business_idea,
                analysis_date=start_time,
                recommended_revenue_models=revenue_recommendations,
                primary_recommendation=primary_recommendation,
                profitability_projections=profitability_projections,
                pricing_insights=pricing_insights,
                market_benchmarks=market_benchmarks,
                competitive_context=self._format_competitive_context_summary(competitive_context),
                persona_context=self._format_persona_context_summary(persona_context),
                market_sizing_context=self._format_market_sizing_context_summary(market_sizing_context),
                implementation_roadmap=implementation_roadmap,
                risk_factors=risk_factors,
                success_metrics=success_metrics,
                execution_time=execution_time
            )
            
            print(f"✅ Business model report generated successfully in {execution_time:.2f} seconds")
            return report
            
        except Exception as e:
            print(f"Error generating business model report: {e}")
            return await self._create_fallback_report(business_input)
    
    async def _generate_pricing_insights(
        self,
        business_input: BusinessModelInput,
        revenue_model: RevenueModelRecommendation,
        competitive_context: Optional[Dict[str, Any]],
        persona_context: Optional[Dict[str, Any]],
        market_sizing_context: Optional[Dict[str, Any]]
    ) -> PricingInsights:
        """Generate AI-powered pricing strategy insights"""
        try:
            # Format contexts for pricing analysis
            competitive_intel = self._format_context_for_pricing(competitive_context, "competitive")
            persona_intel = self._format_context_for_pricing(persona_context, "persona")
            market_intel = self._format_context_for_pricing(market_sizing_context, "market_sizing")
            
            chain = self.pricing_prompt | self.llm | self.parser
            
            result = await asyncio.to_thread(
                chain.invoke,
                {
                    "business_idea": business_input.business_idea,
                    "industry": business_input.industry,
                    "target_market": business_input.target_market,
                    "competitive_context": competitive_intel,
                    "persona_context": persona_intel,
                    "market_sizing_context": market_intel,
                    "revenue_model": revenue_model.model_type.value,
                    "price_point": revenue_model.recommended_price or 29.99
                }
            )
            
            if isinstance(result, dict):
                return self._parse_pricing_insights(result, revenue_model)
            
        except Exception as e:
            print(f"Error generating pricing insights: {e}")
        
        return self._create_fallback_pricing_insights(revenue_model)
    
    async def _generate_market_benchmarks(
        self,
        business_input: BusinessModelInput,
        revenue_model: RevenueModelRecommendation,
        market_intelligence: Dict[str, Any]
    ) -> MarketBenchmarks:
        """Generate market benchmarks using AI and market data"""
        try:
            market_intel_str = self._format_market_intelligence_for_benchmarks(market_intelligence)
            
            chain = self.benchmarks_prompt | self.llm | self.parser
            
            result = await asyncio.to_thread(
                chain.invoke,
                {
                    "business_idea": business_input.business_idea,
                    "industry": business_input.industry,
                    "revenue_model": revenue_model.model_type.value,
                    "market_intelligence": market_intel_str
                }
            )
            
            if isinstance(result, dict):
                return self._parse_market_benchmarks(result)
            
        except Exception as e:
            print(f"Error generating market benchmarks: {e}")
        
        return self._create_fallback_benchmarks()
    
    def _combine_market_intelligence(
        self,
        competitive_context: Optional[Dict[str, Any]],
        persona_context: Optional[Dict[str, Any]],
        market_sizing_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Combine all market intelligence into a unified structure"""
        intelligence = {}
        
        if competitive_context:
            intelligence["competitive_data"] = competitive_context
        if persona_context:
            intelligence["persona_data"] = persona_context
        if market_sizing_context:
            intelligence["market_sizing_data"] = market_sizing_context
            
        return intelligence
    
    def _format_context_for_pricing(self, context: Optional[Dict[str, Any]], context_type: str) -> str:
        """Format context data for pricing analysis"""
        if not context:
            return f"No {context_type} data available."
        
        if context_type == "competitive" and "pricing_intelligence" in context:
            pricing = context["pricing_intelligence"]
            if pricing.get("average_pricing", {}).get("price_range"):
                return f"Competitor pricing: {pricing['average_pricing']['price_range']}"
        
        elif context_type == "persona" and "personas" in context:
            # Extract pricing sensitivity from personas
            personas = context["personas"]
            return f"Analyzed {len(personas)} customer personas with varying price sensitivities"
        
        elif context_type == "market_sizing" and "tam_sam_som_breakdown" in context:
            breakdown = context["tam_sam_som_breakdown"]
            return f"Market opportunity: TAM ${breakdown.get('tam', 0):,.0f}"
        
        return f"Limited {context_type} data available."
    
    def _format_market_intelligence_for_benchmarks(self, intelligence: Dict[str, Any]) -> str:
        """Format combined market intelligence for benchmarks analysis"""
        intel_parts = []
        
        if "competitive_data" in intelligence:
            comp_data = intelligence["competitive_data"]
            if "pricing_intelligence" in comp_data:
                pricing = comp_data["pricing_intelligence"]
                if pricing.get("average_pricing"):
                    intel_parts.append(f"Competitor pricing data available: {pricing['average_pricing']}")
        
        if "market_sizing_data" in intelligence:
            market_data = intelligence["market_sizing_data"]
            if "market_benchmarks" in market_data:
                benchmarks = market_data["market_benchmarks"]
                intel_parts.append(f"Industry benchmarks: CAC ${benchmarks.get('industry_cac', 'unknown')}")
        
        return "\n".join(intel_parts) if intel_parts else "Limited market intelligence available."
    
    def _parse_pricing_insights(self, result: Dict[str, Any], revenue_model: RevenueModelRecommendation) -> PricingInsights:
        """Parse AI-generated pricing insights"""
        try:
            strategy_str = result.get("recommended_strategy", "competitive").lower()
            strategy = self._map_to_pricing_strategy(strategy_str)
            
            return PricingInsights(
                recommended_strategy=strategy,
                competitive_price_range=result.get("competitive_price_range", revenue_model.price_range),
                suggested_pricing_tiers=result.get("suggested_pricing_tiers", []),
                price_elasticity_insights=result.get("price_elasticity_insights", []),
                optimization_recommendations=result.get("optimization_recommendations", [])
            )
        except Exception as e:
            print(f"Error parsing pricing insights: {e}")
            return self._create_fallback_pricing_insights(revenue_model)
    
    def _parse_market_benchmarks(self, result: Dict[str, Any]) -> MarketBenchmarks:
        """Parse AI-generated market benchmarks"""
        try:
            return MarketBenchmarks(
                industry_cac=result.get("industry_cac"),
                industry_ltv=result.get("industry_ltv"),
                ltv_cac_ratio=result.get("ltv_cac_ratio"),
                industry_churn_rate=result.get("industry_churn_rate"),
                average_revenue_per_user=result.get("average_revenue_per_user"),
                market_growth_rate=result.get("market_growth_rate"),
                competitive_landscape_summary=result.get("competitive_landscape_summary", "")
            )
        except Exception as e:
            print(f"Error parsing market benchmarks: {e}")
            return self._create_fallback_benchmarks()
    
    def _map_to_pricing_strategy(self, strategy_str: str) -> PricingStrategy:
        """Map string to PricingStrategy enum"""
        mapping = {
            "penetration": PricingStrategy.PENETRATION,
            "premium": PricingStrategy.PREMIUM,
            "competitive": PricingStrategy.COMPETITIVE,
            "value_based": PricingStrategy.VALUE_BASED,
            "freemium": PricingStrategy.FREEMIUM,
            "tiered": PricingStrategy.TIERED
        }
        return mapping.get(strategy_str, PricingStrategy.COMPETITIVE)
    
    def _generate_implementation_roadmap(
        self, revenue_model: RevenueModelRecommendation, competitive_context: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Generate implementation roadmap based on revenue model and competitive insights"""
        roadmap = [
            f"Set up {revenue_model.model_type.value} pricing structure",
            "Implement payment processing and billing system",
            "Create pricing page and value proposition messaging"
        ]
        
        # Add competitive insights
        if competitive_context and "positioning_recommendations" in competitive_context:
            recommendations = competitive_context["positioning_recommendations"][:2]
            roadmap.extend([f"Competitive positioning: {rec}" for rec in recommendations])
        
        roadmap.extend([
            "Launch with initial pricing and monitor metrics",
            "Collect customer feedback and iterate pricing",
            "Scale pricing strategy based on market response"
        ])
        
        return roadmap
    
    def _generate_risk_factors(
        self,
        revenue_model: RevenueModelRecommendation,
        competitive_context: Optional[Dict[str, Any]],
        market_sizing_context: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Generate risk factors based on analysis"""
        risks = [
            f"Implementation complexity: {revenue_model.implementation_complexity}",
            f"Time to revenue: {revenue_model.time_to_revenue}"
        ]
        
        # Add model-specific risks
        risks.extend(revenue_model.cons[:2])
        
        # Add competitive risks
        if competitive_context and "competitive_landscape" in competitive_context:
            landscape = competitive_context["competitive_landscape"]
            if landscape.get("barriers_to_entry"):
                risks.append("Market entry barriers exist")
        
        return risks[:5]  # Limit to 5 key risks
    
    def _generate_success_metrics(
        self, revenue_model: RevenueModelRecommendation, benchmarks: MarketBenchmarks
    ) -> List[str]:
        """Generate success metrics to track"""
        metrics = [
            "Monthly Recurring Revenue (MRR) growth",
            "Customer Acquisition Cost (CAC)",
            "Customer Lifetime Value (LTV)",
            "LTV:CAC ratio"
        ]
        
        # Add model-specific metrics
        if revenue_model.model_type.value == "subscription":
            metrics.extend(["Monthly churn rate", "Net revenue retention"])
        elif revenue_model.model_type.value == "freemium":
            metrics.extend(["Free to paid conversion rate", "Feature adoption rate"])
        
        return metrics
    
    def _format_competitive_context_summary(self, context: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Format competitive context for report"""
        if not context:
            return None
        
        return {
            "total_competitors": context.get("total_competitors", 0),
            "key_insights": context.get("key_insights", [])[:3],
            "market_gaps": len(context.get("market_gaps", [])),
            "pricing_intelligence": bool(context.get("pricing_intelligence"))
        }
    
    def _format_persona_context_summary(self, context: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Format persona context for report"""
        if not context:
            return None
        
        return {
            "personas_analyzed": len(context.get("personas", [])),
            "target_segments": bool(context.get("target_segments"))
        }
    
    def _format_market_sizing_context_summary(self, context: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Format market sizing context for report"""
        if not context:
            return None
        
        summary = {}
        if "tam_sam_som_breakdown" in context:
            breakdown = context["tam_sam_som_breakdown"]
            summary["market_size"] = {
                "tam": breakdown.get("tam", 0),
                "sam": breakdown.get("sam", 0),
                "som": breakdown.get("som", 0)
            }
        
        return summary if summary else None
    
    def _create_default_recommendation(self) -> RevenueModelRecommendation:
        """Create default revenue model recommendation"""
        from core.business_model_models import RevenueModelType
        
        return RevenueModelRecommendation(
            model_type=RevenueModelType.SUBSCRIPTION,
            recommended_price=29.99,
            price_range={"min": 9.99, "max": 99.99},
            pros=["Predictable revenue", "Customer lifetime value"],
            cons=["Customer acquisition cost", "Churn management"],
            suitability_score=7.0,
            market_examples=["Industry standard"],
            implementation_complexity="Medium",
            time_to_revenue="1-3 months"
        )
    
    def _create_fallback_pricing_insights(self, revenue_model: RevenueModelRecommendation) -> PricingInsights:
        """Create fallback pricing insights"""
        return PricingInsights(
            recommended_strategy=PricingStrategy.COMPETITIVE,
            competitive_price_range=revenue_model.price_range,
            suggested_pricing_tiers=[
                {"name": "Basic", "price": revenue_model.recommended_price or 29.99, "features": ["Core features"]},
                {"name": "Pro", "price": (revenue_model.recommended_price or 29.99) * 2, "features": ["All features", "Priority support"]}
            ],
            price_elasticity_insights=["Price sensitivity varies by customer segment"],
            optimization_recommendations=["Test different price points", "Monitor conversion rates"]
        )
    
    def _create_fallback_benchmarks(self) -> MarketBenchmarks:
        """Create fallback market benchmarks"""
        return MarketBenchmarks(
            industry_cac=50.0,
            industry_ltv=300.0,
            ltv_cac_ratio=6.0,
            industry_churn_rate=0.05,
            average_revenue_per_user=30.0,
            market_growth_rate=0.15,
            competitive_landscape_summary="Competitive market with established players"
        )
    
    async def _create_fallback_report(self, business_input: BusinessModelInput) -> BusinessModelReport:
        """Create fallback report when generation fails"""
        default_recommendation = self._create_default_recommendation()
        
        return BusinessModelReport(
            business_idea=business_input.business_idea,
            recommended_revenue_models=[default_recommendation],
            primary_recommendation=default_recommendation,
            profitability_projections=[],
            pricing_insights=self._create_fallback_pricing_insights(default_recommendation),
            market_benchmarks=self._create_fallback_benchmarks(),
            implementation_roadmap=["Set up basic revenue model", "Implement payment processing"],
            risk_factors=["Market competition", "Customer acquisition challenges"],
            success_metrics=["Revenue growth", "Customer acquisition"]
        )


# Create singleton instance
business_model_report_service = BusinessModelReportService() 