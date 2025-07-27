import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from core.market_models import (
    MarketSizingReport, MarketSizingInput, MarketData, TAMSAMSOMBreakdown,
    MarketSegment, GeographicBreakdown, MarketTrends, CompetitivePosition,
    RevenueProjection
)
from config.settings import settings


class MarketSizingReportService:
    """Service for generating comprehensive market sizing reports"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model_name="gpt-4",
            temperature=0.3,
            openai_api_key=settings.openai_api_key
        )
        
        # Prompt for market trends analysis
        self.market_trends_prompt = ChatPromptTemplate.from_template("""
        Analyze market trends and generate insights for the following business opportunity:
        
        Business Idea: {business_idea}
        Industry: {industry}
        Target Market: {target_market}
        Geographic Scope: {geographic_scope}
        
        Market Context:
        - Current Market Size: ${market_size:,.0f}
        - Growth Rate: {growth_rate}%
        - Industry Overview: {industry_overview}
        
        Additional Context: {additional_context}
        
        Provide detailed market trends analysis including:
        1. Growth drivers pushing the market forward
        2. Market challenges and obstacles
        3. Emerging trends shaping the future
        4. Technology impact and disruptions
        5. Regulatory factors and compliance considerations
        
        Return as JSON:
        {{
            "growth_drivers": ["<driver1>", "<driver2>", "<driver3>"],
            "market_challenges": ["<challenge1>", "<challenge2>", "<challenge3>"],
            "emerging_trends": ["<trend1>", "<trend2>", "<trend3>"],
            "technology_impact": ["<impact1>", "<impact2>", "<impact3>"],
            "regulatory_factors": ["<factor1>", "<factor2>", "<factor3>"]
        }}
        """)
        
        # Prompt for competitive positioning
        self.competitive_position_prompt = ChatPromptTemplate.from_template("""
        Analyze competitive positioning for this business opportunity using detailed competitive intelligence:
        
        Business Idea: {business_idea}
        Industry: {industry}
        Target Market: {target_market}
        Revenue Model: {revenue_model}
        
        Competitive Intelligence:
        {competitor_context}
        
        Market Context: {market_context}
        
        Based on this detailed competitive analysis, provide strategic positioning insights:
        
        1. MARKET GAPS: Identify specific unmet needs, underserved segments, or areas where competitors are weak
        2. COMPETITIVE ADVANTAGES: Determine potential advantages this business could have based on competitor weaknesses and market opportunities
        3. BARRIERS TO ENTRY: Assess realistic barriers including capital requirements, network effects, regulatory hurdles, and competitive response
        4. KEY SUCCESS FACTORS: Define critical factors for success based on what market leaders excel at and what the market demands
        
        Focus on actionable insights derived from the actual competitive data provided.
        Consider pricing strategies, market positioning opportunities, and differentiation potential.
        
        Return as JSON:
        {{
            "market_gaps": ["<specific_gap1>", "<specific_gap2>", "<specific_gap3>"],
            "competitive_advantages": ["<advantage1>", "<advantage2>", "<advantage3>"],
            "barrier_to_entry": ["<barrier1>", "<barrier2>", "<barrier3>"],
            "key_success_factors": ["<factor1>", "<factor2>", "<factor3>"]
        }}
        """)
        
        # Prompt for executive summary
        self.executive_summary_prompt = ChatPromptTemplate.from_template("""
        Create a compelling executive summary for this market sizing analysis:
        
        Business Idea: {business_idea}
        Industry: {industry}
        Target Market: {target_market}
        
        Key Metrics:
        - TAM: ${tam:,.0f}
        - SAM: ${sam:,.0f}  
        - SOM: ${som:,.0f}
        - Market Growth Rate: {growth_rate}%
        - Confidence Level: {confidence_level}
        
        Market Trends: {market_trends}
        Competitive Position: {competitive_position}
        
        Write a compelling 3-4 paragraph executive summary that:
        1. Introduces the market opportunity
        2. Highlights key market metrics and growth potential
        3. Summarizes competitive positioning and advantages
        4. Concludes with investment appeal and recommendations
        
        Make it investor-ready and compelling while being factual and realistic.
        """)
    
    async def generate_market_sizing_report(
        self,
        analysis_input: MarketSizingInput,
        market_data: MarketData,
        tam_sam_som: TAMSAMSOMBreakdown,
        competitor_context: Optional[Dict[str, Any]] = None,
        persona_context: Optional[Dict[str, Any]] = None
    ) -> MarketSizingReport:
        """
        Generate comprehensive market sizing report
        """
        try:
            print("📝 Generating comprehensive market sizing report...")
            
            # Generate report components in parallel
            tasks = [
                self._generate_market_trends(analysis_input, market_data, competitor_context),
                self._generate_competitive_position(analysis_input, market_data, competitor_context),
                self._generate_market_segments(analysis_input, market_data, persona_context),
                self._generate_geographic_breakdown(analysis_input, market_data),
                self._generate_revenue_projections(analysis_input, tam_sam_som, market_data)
            ]
            
            (market_trends, competitive_position, market_segments, 
             geographic_breakdown, revenue_projections) = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Generate executive summary
            executive_summary = await self._generate_executive_summary(
                analysis_input, tam_sam_som, market_data, market_trends, competitive_position
            )
            
            # Generate investment highlights and recommendations
            investment_highlights = self._generate_investment_highlights(
                tam_sam_som, market_trends, competitive_position, revenue_projections
            )
            
            recommendations = self._generate_recommendations(
                analysis_input, market_trends, competitive_position, tam_sam_som
            )
            
            risk_factors = self._generate_risk_factors(market_trends, competitive_position)
            
            # Create final report
            report = MarketSizingReport(
                executive_summary=executive_summary,
                market_overview=market_data,
                tam_sam_som=tam_sam_som,
                market_segments=market_segments if not isinstance(market_segments, Exception) else [],
                geographic_breakdown=geographic_breakdown if not isinstance(geographic_breakdown, Exception) else [],
                market_trends=market_trends if not isinstance(market_trends, Exception) else MarketTrends(),
                competitive_position=competitive_position if not isinstance(competitive_position, Exception) else CompetitivePosition(),
                revenue_projections=revenue_projections if not isinstance(revenue_projections, Exception) else [],
                investment_highlights=investment_highlights,
                risk_factors=risk_factors,
                recommendations=recommendations,
                methodology=self._generate_methodology_description(analysis_input),
                confidence_level=self._calculate_confidence_level(market_data, tam_sam_som),
                generated_at=datetime.now()
            )
            
            print("✅ Market sizing report generated successfully")
            return report
            
        except Exception as e:
            print(f"Error generating market sizing report: {e}")
            return await self._create_fallback_report(analysis_input, market_data, tam_sam_som)
    
    async def _generate_market_trends(
        self,
        analysis_input: MarketSizingInput,
        market_data: MarketData,
        competitor_context: Optional[Dict[str, Any]]
    ) -> MarketTrends:
        """Generate market trends analysis"""
        try:
            additional_context = ""
            if competitor_context:
                additional_context = f"Competitor insights available: {len(competitor_context.get('competitors', []))} competitors analyzed"
            
            chain = self.market_trends_prompt | self.llm | JsonOutputParser()
            
            result = await asyncio.to_thread(
                chain.invoke,
                {
                    "business_idea": analysis_input.business_idea,
                    "industry": analysis_input.industry,
                    "target_market": analysis_input.target_market,
                    "geographic_scope": analysis_input.geographic_scope.value.replace('_', ' '),
                    "market_size": market_data.market_size_current,
                    "growth_rate": market_data.market_growth_rate,
                    "industry_overview": market_data.industry_overview,
                    "additional_context": additional_context
                }
            )
            
            if isinstance(result, dict):
                return MarketTrends(
                    growth_drivers=result.get("growth_drivers", []),
                    market_challenges=result.get("market_challenges", []),
                    emerging_trends=result.get("emerging_trends", []),
                    technology_impact=result.get("technology_impact", []),
                    regulatory_factors=result.get("regulatory_factors", [])
                )
            
        except Exception as e:
            print(f"Error generating market trends: {e}")
        
        return MarketTrends()
    
    async def _generate_competitive_position(
        self,
        analysis_input: MarketSizingInput,
        market_data: MarketData,
        competitor_context: Optional[Dict[str, Any]]
    ) -> CompetitivePosition:
        """Generate competitive positioning analysis"""
        try:
            # Enhanced competitor context formatting
            competitor_context_str = self._format_enhanced_competitor_context(competitor_context)
            
            market_context_str = f"Market size: ${market_data.market_size_current:,.0f}, Growth: {market_data.market_growth_rate}%"
            
            chain = self.competitive_position_prompt | self.llm | JsonOutputParser()
            
            result = await asyncio.to_thread(
                chain.invoke,
                {
                    "business_idea": analysis_input.business_idea,
                    "industry": analysis_input.industry,
                    "target_market": analysis_input.target_market,
                    "revenue_model": analysis_input.revenue_model.value,
                    "competitor_context": competitor_context_str,
                    "market_context": market_context_str
                }
            )
            
            # If we have detailed competitor context, enhance the results with actual data
            if competitor_context and isinstance(result, dict):
                enhanced_result = self._enhance_competitive_position_with_data(result, competitor_context)
                return CompetitivePosition(
                    market_gaps=enhanced_result.get("market_gaps", []),
                    competitive_advantages=enhanced_result.get("competitive_advantages", []),
                    barrier_to_entry=enhanced_result.get("barrier_to_entry", []),
                    key_success_factors=enhanced_result.get("key_success_factors", [])
                )
            elif isinstance(result, dict):
                return CompetitivePosition(
                    market_gaps=result.get("market_gaps", []),
                    competitive_advantages=result.get("competitive_advantages", []),
                    barrier_to_entry=result.get("barrier_to_entry", []),
                    key_success_factors=result.get("key_success_factors", [])
                )
            
        except Exception as e:
            print(f"Error generating competitive position: {e}")
        
        return CompetitivePosition()
    
    def _format_enhanced_competitor_context(self, competitor_context: Optional[Dict[str, Any]]) -> str:
        """Format enhanced competitor context for competitive positioning analysis"""
        if not competitor_context:
            return "No competitor analysis available"
        
        context_parts = []
        
        # Basic competitor info
        total_competitors = competitor_context.get("total_competitors", 0)
        context_parts.append(f"COMPETITIVE LANDSCAPE: {total_competitors} competitors analyzed")
        
        # Market gaps from competitor analysis
        if competitor_context.get("market_gaps"):
            gaps = [gap.get("description", str(gap)) for gap in competitor_context["market_gaps"][:3]]
            context_parts.append(f"IDENTIFIED MARKET GAPS: {'; '.join(gaps)}")
        
        # Key insights from competitor analysis
        if competitor_context.get("key_insights"):
            insights = competitor_context["key_insights"][:3]
            context_parts.append(f"KEY MARKET INSIGHTS: {'; '.join(insights)}")
        
        # Competitive landscape intelligence
        if competitor_context.get("competitive_landscape"):
            landscape = competitor_context["competitive_landscape"]
            concentration = landscape.get("market_concentration", "unknown")
            context_parts.append(f"MARKET CONCENTRATION: {concentration}")
            
            if landscape.get("market_leaders"):
                leader_count = len(landscape["market_leaders"])
                leaders = [leader["name"] for leader in landscape["market_leaders"][:3]]
                context_parts.append(f"MARKET LEADERS ({leader_count}): {', '.join(leaders)}")
        
        # SWOT-based positioning opportunities
        if competitor_context.get("swot_insights"):
            swot = competitor_context["swot_insights"]
            if swot.get("positioning_gaps"):
                gaps = swot["positioning_gaps"][:3]
                context_parts.append(f"POSITIONING OPPORTUNITIES: {'; '.join(gaps)}")
            
            if swot.get("market_weaknesses"):
                weaknesses = [w["theme"] for w in swot["market_weaknesses"][:3]]
                context_parts.append(f"MARKET WEAKNESS AREAS: {', '.join(weaknesses)}")
        
        # Market sentiment insights
        if competitor_context.get("market_sentiment_insights"):
            sentiment = competitor_context["market_sentiment_insights"]
            satisfaction = sentiment.get("market_satisfaction_level", "unknown")
            context_parts.append(f"MARKET SATISFACTION: {satisfaction}")
            
            if sentiment.get("improvement_opportunities"):
                improvements = sentiment["improvement_opportunities"][:2]
                context_parts.append(f"USER-DRIVEN OPPORTUNITIES: {'; '.join(improvements)}")
        
        # Pricing intelligence
        if competitor_context.get("pricing_intelligence"):
            pricing = competitor_context["pricing_intelligence"]
            if pricing.get("average_pricing", {}).get("price_range"):
                price_range = pricing["average_pricing"]["price_range"]
                context_parts.append(f"COMPETITOR PRICING: {price_range}")
        
        return "\n".join(context_parts)
    
    def _enhance_competitive_position_with_data(self, ai_result: Dict[str, Any], competitor_context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance AI-generated competitive position with actual competitor data"""
        enhanced = ai_result.copy()
        
        # Add market gaps from actual competitor analysis
        if competitor_context.get("market_gaps"):
            actual_gaps = [
                gap.get("description", str(gap)) 
                for gap in competitor_context["market_gaps"]
            ]
            # Combine AI-generated gaps with actual identified gaps
            ai_gaps = enhanced.get("market_gaps", [])
            enhanced["market_gaps"] = list(set(ai_gaps + actual_gaps))
        
        # Add barriers to entry from competitive landscape analysis
        if competitor_context.get("competitive_landscape", {}).get("barriers_to_entry"):
            actual_barriers = [
                f"{barrier['type']}: {barrier['description']}" 
                for barrier in competitor_context["competitive_landscape"]["barriers_to_entry"]
            ]
            ai_barriers = enhanced.get("barrier_to_entry", [])
            enhanced["barrier_to_entry"] = list(set(ai_barriers + actual_barriers))
        
        # Add competitive advantages based on SWOT analysis
        if competitor_context.get("swot_insights", {}).get("positioning_gaps"):
            positioning_advantages = [
                f"Opportunity to differentiate through: {gap.replace('Opportunity to excel in: ', '')}"
                for gap in competitor_context["swot_insights"]["positioning_gaps"][:3]
            ]
            ai_advantages = enhanced.get("competitive_advantages", [])
            enhanced["competitive_advantages"] = list(set(ai_advantages + positioning_advantages))
        
        # Add success factors based on market leader analysis
        if competitor_context.get("competitive_landscape", {}).get("market_leaders"):
            leader_strengths = []
            for leader in competitor_context["competitive_landscape"]["market_leaders"]:
                leader_strengths.extend(leader.get("key_strengths", []))
            
            success_factors = [f"Excellence in: {strength}" for strength in set(leader_strengths[:5])]
            ai_success_factors = enhanced.get("key_success_factors", [])
            enhanced["key_success_factors"] = list(set(ai_success_factors + success_factors))
        
        return enhanced
    
    async def _generate_market_segments(
        self,
        analysis_input: MarketSizingInput,
        market_data: MarketData,
        persona_context: Optional[Dict[str, Any]]
    ) -> List[MarketSegment]:
        """Generate market segmentation analysis"""
        segments = []
        
        try:
            # Use persona context if available to create segments
            if persona_context and "personas" in persona_context:
                personas = persona_context["personas"]
                total_market = market_data.market_size_current
                
                for i, persona in enumerate(personas[:3]):  # Limit to 3 segments
                    segment_size = total_market * (0.4 if i == 0 else 0.3 if i == 1 else 0.3)  # Split market
                    
                    segments.append(MarketSegment(
                        name=persona.get("name", f"Segment {i+1}"),
                        size=segment_size,
                        growth_rate=market_data.market_growth_rate + (i * 1),  # Slight variation
                        demographics=persona.get("demographics", {}),
                        characteristics=persona.get("characteristics", [])
                    ))
            else:
                # Create default segments based on customer type
                if analysis_input.customer_type == "b2b":
                    segments = [
                        MarketSegment(
                            name="Enterprise (1000+ employees)",
                            size=market_data.market_size_current * 0.4,
                            growth_rate=market_data.market_growth_rate,
                            demographics={"company_size": "Large", "decision_process": "Complex"},
                            characteristics=["High budget", "Long sales cycles", "Complex requirements"]
                        ),
                        MarketSegment(
                            name="Mid-Market (100-999 employees)",
                            size=market_data.market_size_current * 0.35,
                            growth_rate=market_data.market_growth_rate + 2,
                            demographics={"company_size": "Medium", "decision_process": "Moderate"},
                            characteristics=["Moderate budget", "Medium sales cycles", "Growing needs"]
                        ),
                        MarketSegment(
                            name="Small Business (<100 employees)",
                            size=market_data.market_size_current * 0.25,
                            growth_rate=market_data.market_growth_rate + 4,
                            demographics={"company_size": "Small", "decision_process": "Fast"},
                            characteristics=["Price sensitive", "Quick decisions", "Simple needs"]
                        )
                    ]
                else:
                    segments = [
                        MarketSegment(
                            name="Early Adopters",
                            size=market_data.market_size_current * 0.2,
                            growth_rate=market_data.market_growth_rate + 5,
                            demographics={"tech_savvy": "High", "age": "25-40"},
                            characteristics=["Innovation focused", "Higher spending", "Tech enthusiasts"]
                        ),
                        MarketSegment(
                            name="Mainstream Market",
                            size=market_data.market_size_current * 0.6,
                            growth_rate=market_data.market_growth_rate,
                            demographics={"tech_savvy": "Medium", "age": "30-55"},
                            characteristics=["Value conscious", "Proven solutions", "Mainstream adoption"]
                        ),
                        MarketSegment(
                            name="Late Adopters",
                            size=market_data.market_size_current * 0.2,
                            growth_rate=market_data.market_growth_rate - 2,
                            demographics={"tech_savvy": "Low", "age": "45+"},
                            characteristics=["Price sensitive", "Simple solutions", "Cautious adoption"]
                        )
                    ]
            
        except Exception as e:
            print(f"Error generating market segments: {e}")
        
        return segments
    
    async def _generate_geographic_breakdown(
        self,
        analysis_input: MarketSizingInput,
        market_data: MarketData
    ) -> List[GeographicBreakdown]:
        """Generate geographic market breakdown"""
        breakdown = []
        
        try:
            total_market = market_data.market_size_current
            
            if analysis_input.geographic_scope == "global":
                breakdown = [
                    GeographicBreakdown(
                        region="North America",
                        market_size=total_market * 0.35,
                        potential_customers=100_000_000,
                        market_maturity="Mature",
                        entry_difficulty="Medium"
                    ),
                    GeographicBreakdown(
                        region="Europe",
                        market_size=total_market * 0.28,
                        potential_customers=80_000_000,
                        market_maturity="Mature",
                        entry_difficulty="Medium-High"
                    ),
                    GeographicBreakdown(
                        region="Asia Pacific",
                        market_size=total_market * 0.25,
                        potential_customers=200_000_000,
                        market_maturity="Growing",
                        entry_difficulty="High"
                    ),
                    GeographicBreakdown(
                        region="Rest of World",
                        market_size=total_market * 0.12,
                        potential_customers=50_000_000,
                        market_maturity="Emerging",
                        entry_difficulty="Very High"
                    )
                ]
            else:
                # Single region breakdown
                region_name = analysis_input.geographic_scope.value.replace('_', ' ').title()
                breakdown = [
                    GeographicBreakdown(
                        region=region_name,
                        market_size=total_market,
                        potential_customers=50_000_000,
                        market_maturity="Mature" if "usa" in analysis_input.geographic_scope.value else "Growing",
                        entry_difficulty="Medium"
                    )
                ]
                
        except Exception as e:
            print(f"Error generating geographic breakdown: {e}")
        
        return breakdown
    
    async def _generate_revenue_projections(
        self,
        analysis_input: MarketSizingInput,
        tam_sam_som: TAMSAMSOMBreakdown,
        market_data: MarketData
    ) -> List[RevenueProjection]:
        """Generate 5-year revenue projections"""
        projections = []
        
        try:
            current_year = datetime.now().year
            som_value = tam_sam_som.som
            growth_rate = market_data.market_growth_rate / 100
            
            # Conservative growth assumptions
            year_1_revenue = som_value * 0.02  # Start with 2% of SOM
            base_customers = 1000
            
            for year in range(5):
                year_number = current_year + year
                
                # Progressive market penetration
                penetration_multiplier = (1 + growth_rate) ** year * (1 + year * 0.5)  # Accelerating growth
                projected_revenue = year_1_revenue * penetration_multiplier
                
                # Calculate customers based on revenue model
                if analysis_input.revenue_model in ["subscription", "freemium"]:
                    arpc = analysis_input.estimated_price_point or 100
                    arpc_annual = arpc * 12  # Monthly to annual
                    projected_customers = int(projected_revenue / arpc_annual) if arpc_annual > 0 else base_customers * (year + 1)
                else:
                    arpc_annual = analysis_input.estimated_price_point or 1000
                    projected_customers = int(projected_revenue / arpc_annual) if arpc_annual > 0 else base_customers * (year + 1)
                
                # Calculate market share
                market_share = (projected_revenue / tam_sam_som.sam) * 100 if tam_sam_som.sam > 0 else 0.1
                
                projections.append(RevenueProjection(
                    year=year_number,
                    projected_customers=projected_customers,
                    average_revenue_per_customer=projected_revenue / projected_customers if projected_customers > 0 else 0,
                    total_revenue=projected_revenue,
                    market_share=min(market_share, 15.0)  # Cap at 15%
                ))
                
        except Exception as e:
            print(f"Error generating revenue projections: {e}")
        
        return projections
    
    async def _generate_executive_summary(
        self,
        analysis_input: MarketSizingInput,
        tam_sam_som: TAMSAMSOMBreakdown,
        market_data: MarketData,
        market_trends: MarketTrends,
        competitive_position: CompetitivePosition
    ) -> str:
        """Generate executive summary"""
        try:
            trends_summary = ", ".join(market_trends.growth_drivers[:3]) if market_trends.growth_drivers else "Strong market fundamentals"
            position_summary = ", ".join(competitive_position.competitive_advantages[:3]) if competitive_position.competitive_advantages else "Strategic market positioning"
            
            chain = self.executive_summary_prompt | self.llm
            
            result = await asyncio.to_thread(
                chain.invoke,
                {
                    "business_idea": analysis_input.business_idea,
                    "industry": analysis_input.industry,
                    "target_market": analysis_input.target_market,
                    "tam": tam_sam_som.tam,
                    "sam": tam_sam_som.sam,
                    "som": tam_sam_som.som,
                    "growth_rate": market_data.market_growth_rate,
                    "confidence_level": market_data.confidence_score,
                    "market_trends": trends_summary,
                    "competitive_position": position_summary
                }
            )
            
            return result.content if hasattr(result, 'content') else str(result)
            
        except Exception as e:
            print(f"Error generating executive summary: {e}")
            return f"Market opportunity analysis for {analysis_input.business_idea} in the {analysis_input.industry} industry reveals a significant addressable market of ${tam_sam_som.tam:,.0f} with strong growth potential."
    
    def _generate_investment_highlights(
        self,
        tam_sam_som: TAMSAMSOMBreakdown,
        market_trends: MarketTrends,
        competitive_position: CompetitivePosition,
        revenue_projections: List[RevenueProjection]
    ) -> List[str]:
        """Generate investment highlights"""
        highlights = []
        
        # Market size highlights
        if tam_sam_som.tam > 1_000_000_000:
            highlights.append(f"Large addressable market of ${tam_sam_som.tam:,.0f} billion")
        
        if tam_sam_som.market_penetration_rate > 5:
            highlights.append(f"Achievable market penetration rate of {tam_sam_som.market_penetration_rate:.1f}%")
        
        # Growth highlights
        if market_trends.growth_drivers:
            highlights.append(f"Strong growth drivers: {', '.join(market_trends.growth_drivers[:2])}")
        
        # Competitive highlights
        if competitive_position.competitive_advantages:
            highlights.append(f"Key competitive advantages: {', '.join(competitive_position.competitive_advantages[:2])}")
        
        # Revenue projections
        if revenue_projections and len(revenue_projections) >= 5:
            year_5_revenue = revenue_projections[4].total_revenue
            highlights.append(f"Projected 5-year revenue of ${year_5_revenue:,.0f}")
        
        return highlights[:5]  # Limit to 5 highlights
    
    def _generate_recommendations(
        self,
        analysis_input: MarketSizingInput,
        market_trends: MarketTrends,
        competitive_position: CompetitivePosition,
        tam_sam_som: TAMSAMSOMBreakdown
    ) -> List[str]:
        """Generate strategic recommendations"""
        recommendations = []
        
        # Market entry recommendations
        if competitive_position.market_gaps:
            recommendations.append(f"Focus on market gaps: {competitive_position.market_gaps[0]}")
        
        # Growth strategy
        if market_trends.growth_drivers:
            recommendations.append(f"Leverage growth driver: {market_trends.growth_drivers[0]}")
        
        # Competitive strategy
        if competitive_position.competitive_advantages:
            recommendations.append(f"Emphasize competitive advantage: {competitive_position.competitive_advantages[0]}")
        
        # Market sizing recommendations
        if tam_sam_som.market_penetration_rate < 10:
            recommendations.append("Conservative market penetration strategy recommended given competitive landscape")
        else:
            recommendations.append("Aggressive growth strategy viable given market opportunity")
        
        # Risk mitigation
        if market_trends.market_challenges:
            recommendations.append(f"Address key market challenge: {market_trends.market_challenges[0]}")
        
        return recommendations[:5]  # Limit to 5 recommendations
    
    def _generate_risk_factors(
        self,
        market_trends: MarketTrends,
        competitive_position: CompetitivePosition
    ) -> List[str]:
        """Generate risk factors"""
        risks = []
        
        # Market risks
        if market_trends.market_challenges:
            risks.extend([f"Market challenge: {challenge}" for challenge in market_trends.market_challenges[:2]])
        
        # Competitive risks
        if competitive_position.barrier_to_entry:
            risks.extend([f"Entry barrier: {barrier}" for barrier in competitive_position.barrier_to_entry[:2]])
        
        # Technology risks
        if market_trends.technology_impact:
            risks.append(f"Technology disruption: {market_trends.technology_impact[0]}")
        
        # Regulatory risks
        if market_trends.regulatory_factors:
            risks.append(f"Regulatory factor: {market_trends.regulatory_factors[0]}")
        
        # Default risks if none identified
        if not risks:
            risks = [
                "Market competition and saturation",
                "Economic downturns affecting demand",
                "Technology disruption risks"
            ]
        
        return risks[:5]  # Limit to 5 risks
    
    def _generate_methodology_description(self, analysis_input: MarketSizingInput) -> str:
        """Generate methodology description"""
        return f"""
        This market sizing analysis was conducted using a hybrid approach combining:
        1. AI-powered market research and data synthesis
        2. Top-down market analysis using industry data and reports
        3. Bottom-up calculations based on customer segments and pricing
        4. Competitive analysis integration for market positioning
        5. Persona analysis integration for customer insights
        
        The analysis covers {analysis_input.geographic_scope.value.replace('_', ' ')} market for {analysis_input.customer_type.value} customers 
        in the {analysis_input.industry} industry using a {analysis_input.revenue_model.value} revenue model.
        """
    
    def _calculate_confidence_level(self, market_data: MarketData, tam_sam_som: TAMSAMSOMBreakdown) -> str:
        """Calculate overall confidence level"""
        score = market_data.confidence_score
        
        if score >= 0.8:
            return "High"
        elif score >= 0.6:
            return "Medium-High"
        elif score >= 0.4:
            return "Medium"
        elif score >= 0.2:
            return "Medium-Low"
        else:
            return "Low"
    
    async def _create_fallback_report(
        self,
        analysis_input: MarketSizingInput,
        market_data: MarketData,
        tam_sam_som: TAMSAMSOMBreakdown
    ) -> MarketSizingReport:
        """Create fallback report when generation fails"""
        
        return MarketSizingReport(
            executive_summary=f"Market analysis for {analysis_input.business_idea} reveals a ${tam_sam_som.tam:,.0f} addressable market opportunity.",
            market_overview=market_data,
            tam_sam_som=tam_sam_som,
            market_segments=[],
            geographic_breakdown=[],
            market_trends=MarketTrends(),
            competitive_position=CompetitivePosition(),
            revenue_projections=[],
            investment_highlights=["Significant market opportunity identified"],
            risk_factors=["Standard market risks apply"],
            recommendations=["Conduct detailed market validation"],
            methodology="Fallback analysis methodology applied",
            confidence_level="Medium",
            generated_at=datetime.now()
        )


# Create singleton instance
market_sizing_report_service = MarketSizingReportService() 