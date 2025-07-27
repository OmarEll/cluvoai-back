import asyncio
import json
from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from core.competitor_models import (
    CompetitorAnalysis, MarketSentiment, MarketGap, BusinessInput
)
from config.settings import settings


class MarketAnalysisService:
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.openai_api_key,
            model=settings.llm_model,
            temperature=0.3
        )
        
        self.swot_analysis_prompt = ChatPromptTemplate.from_template("""
        Analyze this competitor and create a SWOT analysis:
        
        Company: {company_name}
        Description: {description}
        Financial Data: {financial_data}
        Pricing Data: {pricing_data}
        Market Position: {market_position}
        
        Provide 3-4 items for each SWOT category that are specific and actionable.
        Focus on business-relevant insights that would help an entrepreneur understand this competitor.
        
        Return as JSON:
        {{
            "strengths": ["strength1", "strength2", "strength3"],
            "weaknesses": ["weakness1", "weakness2", "weakness3"], 
            "opportunities": ["opportunity1", "opportunity2", "opportunity3"],
            "threats": ["threat1", "threat2", "threat3"]
        }}
        """)
        
        self.market_gaps_prompt = ChatPromptTemplate.from_template("""
        Based on this competitive analysis, identify market gaps and opportunities:
        
        Business Idea: {business_idea}
        Competitor Analysis: {competitor_data}
        
        Identify 5 specific market gaps across these categories:
        1. UNDERSERVED SEGMENTS - customer groups not well served
        2. FEATURE GAPS - missing features across competitors  
        3. PRICING GAPS - pricing models or tiers missing
        4. GEOGRAPHIC GAPS - underserved markets/regions
        5. POSITIONING GAPS - unique positioning opportunities
        
        For each gap, provide:
        - category (one of the 5 above)
        - description (specific gap identified)
        - opportunity_score (1-10 rating)
        - recommended_action (specific action to take)
        
        Return as JSON array:
        [
            {{
                "category": "UNDERSERVED SEGMENTS",
                "description": "Small businesses under 10 employees lack affordable solutions",
                "opportunity_score": 8.5,
                "recommended_action": "Create a simplified, low-cost tier for micro-businesses"
            }}
        ]
        """)
        
        self.sentiment_analysis_prompt = ChatPromptTemplate.from_template("""
        Analyze market sentiment for: {company_name}
        
        Based on this data:
        {sentiment_data}
        
        Provide:
        1. Overall sentiment score (-1 to 1, where -1 is very negative, 1 is very positive)
        2. Top 3 customer complaints
        3. Top 3 customer praises
        4. Key sentiment themes
        
        Return as JSON:
        {{
            "overall_score": 0.3,
            "key_complaints": ["complaint1", "complaint2", "complaint3"],
            "key_praises": ["praise1", "praise2", "praise3"]
        }}
        """)

    async def analyze_competitor_swot(self, competitor_analysis: CompetitorAnalysis) -> CompetitorAnalysis:
        """
        Generate SWOT analysis for a competitor
        """
        try:
            chain = self.swot_analysis_prompt | self.llm | JsonOutputParser()
            
            result = await asyncio.to_thread(
                chain.invoke,
                {
                    "company_name": competitor_analysis.basic_info.name,
                    "description": competitor_analysis.basic_info.description,
                    "financial_data": json.dumps(competitor_analysis.financial_data.dict(), indent=2),
                    "pricing_data": json.dumps(competitor_analysis.pricing_data.dict(), indent=2),
                    "market_position": competitor_analysis.basic_info.type.value
                }
            )
            
            # Update competitor analysis with SWOT
            competitor_analysis.strengths = result.get("strengths", [])
            competitor_analysis.weaknesses = result.get("weaknesses", [])
            competitor_analysis.opportunities = result.get("opportunities", [])
            competitor_analysis.threats = result.get("threats", [])
            
            return competitor_analysis
            
        except Exception as e:
            print(f"SWOT analysis failed for {competitor_analysis.basic_info.name}: {e}")
            
            # Fallback SWOT based on data
            competitor_analysis.strengths = self._generate_fallback_strengths(competitor_analysis)
            competitor_analysis.weaknesses = self._generate_fallback_weaknesses(competitor_analysis)
            competitor_analysis.opportunities = ["Market expansion", "Product improvement", "Partnership opportunities"]
            competitor_analysis.threats = ["New competitors", "Market saturation", "Technology disruption"]
            
            return competitor_analysis

    async def identify_market_gaps(self, business_input: BusinessInput, competitors: List[CompetitorAnalysis]) -> List[MarketGap]:
        """
        Identify market gaps and opportunities
        """
        try:
            # Prepare competitor data for analysis
            competitor_summary = []
            for comp in competitors:
                competitor_summary.append({
                    "name": comp.basic_info.name,
                    "type": comp.basic_info.type.value,
                    "pricing": comp.pricing_data.monthly_price,
                    "employees": comp.financial_data.employee_count,
                    "strengths": comp.strengths,
                    "weaknesses": comp.weaknesses
                })
            
            chain = self.market_gaps_prompt | self.llm | JsonOutputParser()
            
            result = await asyncio.to_thread(
                chain.invoke,
                {
                    "business_idea": business_input.idea_description,
                    "competitor_data": json.dumps(competitor_summary, indent=2)
                }
            )
            
            gaps = []
            for gap_data in result:
                if isinstance(gap_data, dict):
                    gaps.append(MarketGap(
                        category=gap_data.get("category", "GENERAL"),
                        description=gap_data.get("description", ""),
                        opportunity_score=float(gap_data.get("opportunity_score", 5.0)),
                        recommended_action=gap_data.get("recommended_action", "")
                    ))
            
            return gaps
            
        except Exception as e:
            print(f"Market gap analysis failed: {e}")
            return self._generate_fallback_gaps()

    async def analyze_market_sentiment(self, competitor_name: str, sentiment_data: dict) -> MarketSentiment:
        """
        Analyze market sentiment for a competitor
        """
        try:
            chain = self.sentiment_analysis_prompt | self.llm | JsonOutputParser()
            
            result = await asyncio.to_thread(
                chain.invoke,
                {
                    "company_name": competitor_name,
                    "sentiment_data": json.dumps(sentiment_data, indent=2)
                }
            )
            
            return MarketSentiment(
                overall_score=float(result.get("overall_score", 0.0)),
                reddit_mentions=sentiment_data.get("reddit_mentions", 0),
                twitter_mentions=sentiment_data.get("twitter_mentions", 0),
                key_complaints=result.get("key_complaints", []),
                key_praises=result.get("key_praises", [])
            )
            
        except Exception as e:
            print(f"Sentiment analysis failed for {competitor_name}: {e}")
            return MarketSentiment(
                overall_score=0.0,
                reddit_mentions=sentiment_data.get("reddit_mentions", 0),
                twitter_mentions=sentiment_data.get("twitter_mentions", 0),
                key_complaints=["No sentiment data available"],
                key_praises=["Analysis unavailable"]
            )

    def _generate_fallback_strengths(self, competitor: CompetitorAnalysis) -> List[str]:
        """
        Generate fallback strengths based on available data
        """
        strengths = []
        
        if competitor.financial_data.funding_total:
            strengths.append("Well-funded with strong financial backing")
        
        if competitor.financial_data.employee_count and competitor.financial_data.employee_count > 100:
            strengths.append("Large team with significant resources")
        
        if competitor.pricing_data.free_tier:
            strengths.append("Freemium model attracts users")
        
        if competitor.basic_info.type.value == "direct":
            strengths.append("Established market presence")
        
        if not strengths:
            strengths = ["Market presence", "Product offering", "Customer base"]
        
        return strengths

    def _generate_fallback_weaknesses(self, competitor: CompetitorAnalysis) -> List[str]:
        """
        Generate fallback weaknesses based on available data
        """
        weaknesses = []
        
        if not competitor.financial_data.funding_total:
            weaknesses.append("Limited funding information suggests possible resource constraints")
        
        if competitor.pricing_data.monthly_price and competitor.pricing_data.monthly_price > 50:
            weaknesses.append("Higher pricing may limit market accessibility")
        
        if competitor.financial_data.employee_count and competitor.financial_data.employee_count < 20:
            weaknesses.append("Small team may limit scaling capabilities")
        
        if not weaknesses:
            weaknesses = ["Market competition", "Customer acquisition costs", "Product differentiation"]
        
        return weaknesses

    def _generate_fallback_gaps(self) -> List[MarketGap]:
        """
        Generate fallback market gaps
        """
        return [
            MarketGap(
                category="PRICING GAPS",
                description="Affordable solutions for small businesses",
                opportunity_score=7.5,
                recommended_action="Develop a low-cost tier targeting SMBs"
            ),
            MarketGap(
                category="FEATURE GAPS", 
                description="AI-powered automation features",
                opportunity_score=8.0,
                recommended_action="Integrate advanced AI capabilities"
            ),
            MarketGap(
                category="UNDERSERVED SEGMENTS",
                description="Industry-specific solutions",
                opportunity_score=6.5,
                recommended_action="Create vertical-specific product versions"
            )
        ]