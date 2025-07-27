import asyncio
import aiohttp
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from core.market_models import MarketData, GeographicScope, CustomerType, RevenueModel, MarketSizingInput
from config.settings import settings


class MarketDataCollectionService:
    """Service for collecting market data from various sources"""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model_name="gpt-4",
            temperature=0.3,
            openai_api_key=settings.openai_api_key
        )
        
        # Research prompt for market data collection
        self.market_research_prompt = ChatPromptTemplate.from_template("""
        You are a professional market research analyst. Analyze the following business idea and provide comprehensive market data.
        
        Business Idea: {business_idea}
        Industry: {industry}
        Target Market: {target_market}
        Geographic Scope: {geographic_scope}
        Customer Type: {customer_type}
        
        Additional Context: {additional_context}
        
        Provide a detailed market analysis including:
        1. Industry overview and current market size
        2. Historical growth rates (3-5 years)
        3. Projected growth rates for next 5 years
        4. Key market drivers and trends
        5. Major challenges facing the industry
        6. Technology disruptions and their impact
        7. Regulatory environment
        8. Customer behavior patterns
        9. Pricing trends in the market
        10. Market maturity level
        
        Base your analysis on known industry data, reports, and market intelligence.
        Be specific with numbers where possible and cite reasoning for estimates.
        
        Return as JSON with detailed market insights.
        """)
        
        # Industry data sources for web scraping
        self.data_sources = {
            "industry_reports": [
                "https://www.ibisworld.com",
                "https://www.statista.com", 
                "https://www.grandviewresearch.com",
                "https://www.fortunebusinessinsights.com"
            ],
            "market_news": [
                "https://www.marketwatch.com",
                "https://www.bloomberg.com",
                "https://techcrunch.com",
                "https://www.reuters.com"
            ],
            "government_data": [
                "https://www.census.gov",
                "https://data.gov",
                "https://fred.stlouisfed.org"
            ]
        }
    
    async def collect_market_data(
        self, 
        analysis_input: MarketSizingInput,
        additional_context: str = ""
    ) -> MarketData:
        """
        Main method to collect comprehensive market data
        """
        try:
            print("🔍 Collecting market data from multiple sources...")
            
            # Parallel data collection from different sources
            tasks = [
                self._ai_market_research(analysis_input, additional_context),
                self._web_scraping_research(analysis_input),
                self._industry_specific_research(analysis_input)
            ]
            
            ai_research, web_data, industry_data = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine and synthesize data
            market_data = await self._synthesize_market_data(
                analysis_input, ai_research, web_data, industry_data
            )
            
            return market_data
            
        except Exception as e:
            print(f"Error collecting market data: {e}")
            # Return fallback data
            return await self._create_fallback_market_data(analysis_input)
    
    async def _ai_market_research(
        self, 
        analysis_input: MarketSizingInput, 
        additional_context: str
    ) -> Dict[str, Any]:
        """Use AI to generate market research insights"""
        try:
            chain = self.market_research_prompt | self.llm | JsonOutputParser()
            
            result = await asyncio.to_thread(
                chain.invoke,
                {
                    "business_idea": analysis_input.business_idea,
                    "industry": analysis_input.industry,
                    "target_market": analysis_input.target_market,
                    "geographic_scope": analysis_input.geographic_scope.value,
                    "customer_type": analysis_input.customer_type.value,
                    "additional_context": additional_context
                }
            )
            
            return result if isinstance(result, dict) else {}
            
        except Exception as e:
            print(f"Error in AI market research: {e}")
            return {}
    
    async def _web_scraping_research(self, analysis_input: MarketSizingInput) -> Dict[str, Any]:
        """Scrape web sources for market data"""
        scraped_data = {
            "industry_reports": [],
            "market_news": [],
            "statistical_data": []
        }
        
        try:
            # Search for industry-specific information
            search_queries = [
                f"{analysis_input.industry} market size",
                f"{analysis_input.industry} growth rate",
                f"{analysis_input.target_market} market trends",
                f"{analysis_input.industry} industry report 2024"
            ]
            
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={'User-Agent': 'Mozilla/5.0 (compatible; MarketResearchBot/1.0)'}
            ) as session:
                
                for query in search_queries:
                    try:
                        # Use a search engine API or direct scraping
                        data = await self._search_market_data(session, query)
                        if data:
                            scraped_data["industry_reports"].extend(data)
                    except Exception as e:
                        print(f"Error scraping for query '{query}': {e}")
                        continue
                        
        except Exception as e:
            print(f"Error in web scraping: {e}")
        
        return scraped_data
    
    async def _search_market_data(self, session: aiohttp.ClientSession, query: str) -> List[Dict]:
        """Search for market data using web scraping"""
        try:
            # For demo purposes, we'll simulate market data search
            # In production, you'd integrate with APIs like:
            # - Google Custom Search API
            # - Bing Search API
            # - Industry-specific APIs
            
            # Simulate realistic market data based on query
            if "market size" in query.lower():
                return [
                    {
                        "source": "Industry Report",
                        "data": f"Market size data for {query}",
                        "value": "Estimated market size based on industry analysis",
                        "confidence": 0.7
                    }
                ]
            elif "growth rate" in query.lower():
                return [
                    {
                        "source": "Growth Analysis",
                        "data": f"Growth trends for {query}",
                        "value": "Historical and projected growth rates",
                        "confidence": 0.8
                    }
                ]
            
            return []
            
        except Exception as e:
            print(f"Error searching for '{query}': {e}")
            return []
    
    async def _industry_specific_research(self, analysis_input: MarketSizingInput) -> Dict[str, Any]:
        """Conduct industry-specific research"""
        industry_data = {
            "market_characteristics": {},
            "key_metrics": {},
            "benchmarks": {}
        }
        
        try:
            # Industry-specific research logic
            industry = analysis_input.industry.lower()
            
            if "software" in industry or "tech" in industry:
                industry_data["market_characteristics"] = {
                    "typical_growth_rate": "15-25% annually",
                    "customer_acquisition_cost": "High initial, decreasing with scale",
                    "revenue_model": "Subscription-based dominant",
                    "market_concentration": "High competition, winner-takes-most"
                }
            elif "retail" in industry or "e-commerce" in industry:
                industry_data["market_characteristics"] = {
                    "typical_growth_rate": "8-12% annually",
                    "customer_acquisition_cost": "Medium, channel-dependent",
                    "revenue_model": "Transaction-based",
                    "market_concentration": "Fragmented with major players"
                }
            elif "healthcare" in industry or "biotech" in industry:
                industry_data["market_characteristics"] = {
                    "typical_growth_rate": "5-10% annually",
                    "customer_acquisition_cost": "Very high due to regulations",
                    "revenue_model": "Mixed: insurance, direct pay, licensing",
                    "market_concentration": "Regulated, high barriers"
                }
            else:
                industry_data["market_characteristics"] = {
                    "typical_growth_rate": "3-8% annually",
                    "customer_acquisition_cost": "Industry-dependent",
                    "revenue_model": "Mixed models",
                    "market_concentration": "Varies by segment"
                }
                
        except Exception as e:
            print(f"Error in industry-specific research: {e}")
        
        return industry_data
    
    async def _synthesize_market_data(
        self,
        analysis_input: MarketSizingInput,
        ai_research: Dict[str, Any],
        web_data: Dict[str, Any],
        industry_data: Dict[str, Any]
    ) -> MarketData:
        """Synthesize collected data into structured market data"""
        
        try:
            # Extract market size from various sources
            market_size = self._extract_market_size(ai_research, web_data, industry_data)
            
            # Extract growth rates
            growth_rate = self._extract_growth_rate(ai_research, web_data, industry_data)
            projected_growth = self._extract_projected_growth(ai_research, web_data, industry_data)
            
            # Create industry overview
            industry_overview = self._create_industry_overview(
                analysis_input, ai_research, industry_data
            )
            
            # Compile data sources
            data_sources = []
            if ai_research:
                data_sources.append("AI Market Analysis")
            if web_data.get("industry_reports"):
                data_sources.append("Industry Reports")
            if industry_data:
                data_sources.append("Industry Benchmarks")
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(ai_research, web_data, industry_data)
            
            return MarketData(
                industry_overview=industry_overview,
                market_size_current=market_size,
                market_growth_rate=growth_rate,
                projected_growth_rate=projected_growth,
                data_sources=data_sources,
                confidence_score=confidence_score,
                last_updated=datetime.now()
            )
            
        except Exception as e:
            print(f"Error synthesizing market data: {e}")
            return await self._create_fallback_market_data(analysis_input)
    
    def _extract_market_size(self, ai_research: Dict, web_data: Dict, industry_data: Dict) -> float:
        """Extract market size from collected data"""
        try:
            # Try to extract from AI research first
            if ai_research and isinstance(ai_research, dict):
                market_size_str = str(ai_research.get("current_market_size", ""))
                size = self._parse_market_size(market_size_str)
                if size > 0:
                    return size
            
            # Use industry benchmarks for estimation
            industry_chars = industry_data.get("market_characteristics", {})
            if industry_chars:
                # Return a reasonable estimate based on industry type
                return 10_000_000_000  # $10B default for major industries
                
            # Fallback
            return 1_000_000_000  # $1B conservative estimate
            
        except Exception:
            return 1_000_000_000
    
    def _extract_growth_rate(self, ai_research: Dict, web_data: Dict, industry_data: Dict) -> float:
        """Extract historical growth rate"""
        try:
            if ai_research and isinstance(ai_research, dict):
                growth_str = str(ai_research.get("historical_growth_rate", ""))
                growth = self._parse_percentage(growth_str)
                if growth > 0:
                    return growth
            
            # Use industry defaults
            industry_chars = industry_data.get("market_characteristics", {})
            typical_growth = industry_chars.get("typical_growth_rate", "5-10% annually")
            return self._parse_percentage(typical_growth)
            
        except Exception:
            return 5.0  # 5% default
    
    def _extract_projected_growth(self, ai_research: Dict, web_data: Dict, industry_data: Dict) -> float:
        """Extract projected growth rate"""
        try:
            if ai_research and isinstance(ai_research, dict):
                projected_str = str(ai_research.get("projected_growth_rate", ""))
                growth = self._parse_percentage(projected_str)
                if growth > 0:
                    return growth
            
            # Default to slightly higher than historical
            historical = self._extract_growth_rate(ai_research, web_data, industry_data)
            return min(historical * 1.2, 25.0)  # Cap at 25%
            
        except Exception:
            return 6.0  # 6% default
    
    def _parse_market_size(self, size_str: str) -> float:
        """Parse market size from string"""
        try:
            # Look for billion/million indicators
            size_str = size_str.lower().replace(",", "").replace("$", "")
            
            if "billion" in size_str or "b" in size_str:
                numbers = re.findall(r'\d+\.?\d*', size_str)
                if numbers:
                    return float(numbers[0]) * 1_000_000_000
                    
            elif "million" in size_str or "m" in size_str:
                numbers = re.findall(r'\d+\.?\d*', size_str)
                if numbers:
                    return float(numbers[0]) * 1_000_000
            
            # Try to extract raw number
            numbers = re.findall(r'\d+\.?\d*', size_str)
            if numbers:
                return float(numbers[0])
                
        except Exception:
            pass
        
        return 0.0
    
    def _parse_percentage(self, percent_str: str) -> float:
        """Parse percentage from string"""
        try:
            # Extract first number that looks like a percentage
            numbers = re.findall(r'\d+\.?\d*', percent_str.replace("%", ""))
            if numbers:
                return float(numbers[0])
        except Exception:
            pass
        
        return 0.0
    
    def _create_industry_overview(
        self, 
        analysis_input: MarketSizingInput, 
        ai_research: Dict, 
        industry_data: Dict
    ) -> str:
        """Create comprehensive industry overview"""
        
        overview_parts = [
            f"The {analysis_input.industry} industry serves {analysis_input.target_market} "
            f"in the {analysis_input.geographic_scope.value.replace('_', ' ')} market."
        ]
        
        if ai_research and isinstance(ai_research, dict):
            if "industry_overview" in ai_research:
                overview_parts.append(str(ai_research["industry_overview"]))
        
        if industry_data and "market_characteristics" in industry_data:
            chars = industry_data["market_characteristics"]
            overview_parts.append(
                f"This industry typically experiences {chars.get('typical_growth_rate', 'moderate growth')} "
                f"with {chars.get('market_concentration', 'varied market concentration')}."
            )
        
        return " ".join(overview_parts)
    
    def _calculate_confidence_score(self, ai_research: Dict, web_data: Dict, industry_data: Dict) -> float:
        """Calculate confidence score based on data quality"""
        score = 0.0
        
        if ai_research and isinstance(ai_research, dict) and ai_research:
            score += 0.4
        
        if web_data and any(web_data.values()):
            score += 0.3
            
        if industry_data and any(industry_data.values()):
            score += 0.3
        
        return min(score, 1.0)
    
    async def _create_fallback_market_data(self, analysis_input: MarketSizingInput) -> MarketData:
        """Create fallback market data when collection fails"""
        return MarketData(
            industry_overview=f"Market analysis for {analysis_input.industry} targeting {analysis_input.target_market}.",
            market_size_current=1_000_000_000,  # $1B default
            market_growth_rate=5.0,  # 5% default
            projected_growth_rate=6.0,  # 6% default
            data_sources=["Fallback Analysis"],
            confidence_score=0.3,
            last_updated=datetime.now()
        )


# Create singleton instance
market_data_service = MarketDataCollectionService() 