import asyncio
import json
from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from core.competitor_models import (
    BusinessInput, CompetitorAnalysis, MarketGap, CompetitorReport
)
from config.settings import settings


class ReportGenerationService:
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.openai_api_key,
            model=settings.llm_model,
            temperature=0.3
        )
        
        self.insights_prompt = ChatPromptTemplate.from_template("""
        Based on this competitive analysis, generate 5 key strategic insights:
        
        Business Idea: {business_idea}
        Competitors Analyzed: {competitor_count}
        Competitor Data: {competitor_summary}
        Market Gaps: {market_gaps}
        
        Provide insights that are:
        1. Actionable for an entrepreneur
        2. Based on the competitive data
        3. Focused on strategic opportunities
        4. Specific and measurable where possible
        5. Prioritized by potential impact
        
        Return as JSON array of strings:
        ["insight1", "insight2", "insight3", "insight4", "insight5"]
        """)
        
        self.positioning_prompt = ChatPromptTemplate.from_template("""
        Generate positioning recommendations for this business idea:
        
        Business Idea: {business_idea}
        Competitive Landscape: {competitive_landscape}
        Identified Gaps: {market_gaps}
        
        Provide 5 specific positioning recommendations:
        1. How to differentiate from competitors
        2. Target market positioning
        3. Pricing strategy recommendations  
        4. Feature/product positioning
        5. Go-to-market positioning
        
        Each recommendation should be actionable and specific.
        
        Return as JSON array of strings:
        ["recommendation1", "recommendation2", "recommendation3", "recommendation4", "recommendation5"]
        """)

    async def generate_report(
        self, 
        business_input: BusinessInput,
        competitors: List[CompetitorAnalysis],
        market_gaps: List[MarketGap],
        errors: List[str]
    ) -> CompetitorReport:
        """
        Generate comprehensive competitive intelligence report
        """
        try:
            # Generate insights and recommendations in parallel
            insights_task = self._generate_insights(business_input, competitors, market_gaps)
            positioning_task = self._generate_positioning(business_input, competitors, market_gaps)
            
            key_insights, positioning_recs = await asyncio.gather(
                insights_task, 
                positioning_task,
                return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(key_insights, Exception):
                key_insights = self._generate_fallback_insights(competitors)
                
            if isinstance(positioning_recs, Exception):
                positioning_recs = self._generate_fallback_positioning()
            
            # Create the report
            report = CompetitorReport(
                business_idea=business_input.idea_description,
                total_competitors=len(competitors),
                competitors=competitors,
                market_gaps=market_gaps,
                key_insights=key_insights,
                positioning_recommendations=positioning_recs,
                execution_time=0.0  # Will be set by workflow
            )
            
            return report
            
        except Exception as e:
            print(f"Report generation failed: {e}")
            return self._generate_fallback_report(business_input, competitors, market_gaps)

    async def _generate_insights(
        self, 
        business_input: BusinessInput,
        competitors: List[CompetitorAnalysis], 
        market_gaps: List[MarketGap]
    ) -> List[str]:
        """
        Generate strategic insights using AI
        """
        try:
            # Prepare competitor summary
            competitor_summary = []
            for comp in competitors:
                competitor_summary.append({
                    "name": comp.basic_info.name,
                    "type": comp.basic_info.type.value,
                    "funding": comp.financial_data.funding_total,
                    "employees": comp.financial_data.employee_count,
                    "pricing": comp.pricing_data.monthly_price,
                    "strengths": comp.strengths[:2],  # Top 2 strengths
                    "weaknesses": comp.weaknesses[:2]  # Top 2 weaknesses
                })
            
            chain = self.insights_prompt | self.llm | JsonOutputParser()
            
            result = await asyncio.to_thread(
                chain.invoke,
                {
                    "business_idea": business_input.idea_description,
                    "competitor_count": len(competitors),
                    "competitor_summary": json.dumps(competitor_summary, indent=2),
                    "market_gaps": json.dumps([gap.dict() for gap in market_gaps], indent=2)
                }
            )
            
            if isinstance(result, list):
                return result[:5]  # Max 5 insights
            else:
                return self._generate_fallback_insights(competitors)
                
        except Exception as e:
            print(f"Insights generation failed: {e}")
            return self._generate_fallback_insights(competitors)

    async def _generate_positioning(
        self,
        business_input: BusinessInput,
        competitors: List[CompetitorAnalysis],
        market_gaps: List[MarketGap]
    ) -> List[str]:
        """
        Generate positioning recommendations using AI
        """
        try:
            # Prepare competitive landscape summary
            landscape_summary = {
                "total_competitors": len(competitors),
                "competitor_types": {},
                "pricing_range": self._calculate_pricing_range(competitors),
                "common_strengths": self._identify_common_patterns(competitors, "strengths"),
                "common_weaknesses": self._identify_common_patterns(competitors, "weaknesses")
            }
            
            # Count competitor types
            for comp in competitors:
                comp_type = comp.basic_info.type.value
                landscape_summary["competitor_types"][comp_type] = landscape_summary["competitor_types"].get(comp_type, 0) + 1
            
            chain = self.positioning_prompt | self.llm | JsonOutputParser()
            
            result = await asyncio.to_thread(
                chain.invoke,
                {
                    "business_idea": business_input.idea_description,
                    "competitive_landscape": json.dumps(landscape_summary, indent=2),
                    "market_gaps": json.dumps([gap.dict() for gap in market_gaps], indent=2)
                }
            )
            
            if isinstance(result, list):
                return result[:5]  # Max 5 recommendations
            else:
                return self._generate_fallback_positioning()
                
        except Exception as e:
            print(f"Positioning generation failed: {e}")
            return self._generate_fallback_positioning()

    def _calculate_pricing_range(self, competitors: List[CompetitorAnalysis]) -> dict:
        """
        Calculate pricing statistics from competitors
        """
        prices = []
        for comp in competitors:
            if comp.pricing_data.monthly_price:
                prices.append(comp.pricing_data.monthly_price)
        
        if not prices:
            return {"min": 0, "max": 0, "average": 0}
        
        return {
            "min": min(prices),
            "max": max(prices),
            "average": sum(prices) / len(prices)
        }

    def _identify_common_patterns(self, competitors: List[CompetitorAnalysis], attribute: str) -> List[str]:
        """
        Identify common patterns in competitor strengths/weaknesses
        """
        all_items = []
        for comp in competitors:
            items = getattr(comp, attribute, [])
            all_items.extend(items)
        
        # Simple frequency analysis
        from collections import Counter
        common_items = Counter(all_items).most_common(3)
        return [item[0] for item in common_items]

    def _generate_fallback_insights(self, competitors: List[CompetitorAnalysis]) -> List[str]:
        """
        Generate fallback insights based on basic data analysis
        """
        insights = []
        
        if len(competitors) > 0:
            insights.append(f"Market has {len(competitors)} identified competitors indicating active competition")
            
            # Pricing insights
            prices = [c.pricing_data.monthly_price for c in competitors if c.pricing_data.monthly_price]
            if prices:
                avg_price = sum(prices) / len(prices)
                insights.append(f"Average competitor pricing is ${avg_price:.2f}/month, providing pricing benchmark")
            
            # Funding insights
            funded_competitors = [c for c in competitors if c.financial_data.funding_total and c.financial_data.funding_total != "Unknown"]
            if funded_competitors:
                insights.append(f"{len(funded_competitors)} out of {len(competitors)} competitors have identifiable funding")
            
            # Type distribution
            direct_competitors = [c for c in competitors if c.basic_info.type.value == "direct"]
            insights.append(f"{len(direct_competitors)} direct competitors identified requiring clear differentiation")
        
        # Fill to 5 insights
        while len(insights) < 5:
            fallback_insights = [
                "Competitive landscape analysis reveals market validation for the business concept",
                "Opportunity exists to differentiate through unique value proposition",
                "Market positioning strategy should focus on identified gaps",
                "Customer acquisition strategy should consider competitor approaches",
                "Product development should address competitor weaknesses"
            ]
            insights.append(fallback_insights[len(insights) - len([i for i in insights if i in fallback_insights])])
        
        return insights[:5]

    def _generate_fallback_positioning(self) -> List[str]:
        """
        Generate fallback positioning recommendations
        """
        return [
            "Focus on unique value proposition that differentiates from established competitors",
            "Target underserved customer segments identified in market gap analysis", 
            "Position pricing competitively while maintaining sustainable margins",
            "Emphasize product features that address common competitor weaknesses",
            "Develop go-to-market strategy that leverages identified market opportunities"
        ]

    def _generate_fallback_report(
        self,
        business_input: BusinessInput,
        competitors: List[CompetitorAnalysis],
        market_gaps: List[MarketGap]
    ) -> CompetitorReport:
        """
        Generate fallback report when AI generation fails
        """
        return CompetitorReport(
            business_idea=business_input.idea_description,
            total_competitors=len(competitors),
            competitors=competitors,
            market_gaps=market_gaps,
            key_insights=self._generate_fallback_insights(competitors),
            positioning_recommendations=self._generate_fallback_positioning(),
            execution_time=0.0
        )