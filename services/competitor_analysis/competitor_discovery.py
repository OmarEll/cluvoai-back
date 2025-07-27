import asyncio
from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

from core.competitor_models import BusinessInput, CompetitorBasic, CompetitorType
from config.settings import settings


class CompetitorDiscoveryService:
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.openai_api_key,
            model=settings.llm_model,
            temperature=settings.llm_temperature
        )
        
        self.discovery_prompt = ChatPromptTemplate.from_template("""
        Analyze this business idea and identify competitors:
        
        Business Idea: {idea_description}
        Target Market: {target_market}
        Industry: {industry}
        Geographic Focus: {geographic_focus}
        
        Find exactly {max_competitors} competitors across these categories:
        1. DIRECT competitors (same product, same market)
        2. INDIRECT competitors (different product, same need)
        3. SUBSTITUTE competitors (alternative solutions)
        
        For each competitor, provide:
        - name: Company name
        - domain: Website domain (e.g., "company.com")
        - type: "direct", "indirect", or "substitute"
        - description: Brief description of what they do
        
        Return as JSON array with exactly {max_competitors} objects.
        
        Example format:
        [
            {{"name": "Slack", "domain": "slack.com", "type": "direct", "description": "Team communication platform"}},
            {{"name": "Microsoft Teams", "domain": "teams.microsoft.com", "type": "direct", "description": "Integrated workplace chat and video"}}
        ]
        
        Return only the JSON array, no other text.
        """)

    async def discover_competitors(self, business_input: BusinessInput) -> List[CompetitorBasic]:
        """
        Discover competitors using AI analysis
        """
        try:
            chain = self.discovery_prompt | self.llm | JsonOutputParser()
            
            result = await asyncio.to_thread(
                chain.invoke,
                {
                    "idea_description": business_input.idea_description,
                    "target_market": business_input.target_market or "Not specified",
                    "industry": business_input.industry or "Not specified", 
                    "geographic_focus": business_input.geographic_focus or "Global",
                    "max_competitors": settings.max_competitors
                }
            )
            
            competitors = []
            for comp_data in result[:settings.max_competitors]:
                if isinstance(comp_data, dict) and "name" in comp_data:
                    competitor = CompetitorBasic(
                        name=comp_data.get("name", "Unknown"),
                        domain=self._clean_domain(comp_data.get("domain", "")),
                        type=CompetitorType(comp_data.get("type", "direct")),
                        description=comp_data.get("description", "")
                    )
                    competitors.append(competitor)
            
            # Ensure minimum competitors with fallbacks if needed
            if len(competitors) < settings.min_competitors:
                fallback_competitors = self._get_fallback_competitors(business_input)
                competitors.extend(fallback_competitors[:settings.min_competitors - len(competitors)])
            
            return competitors[:settings.max_competitors]
            
        except Exception as e:
            print(f"Competitor discovery failed: {e}")
            return self._get_fallback_competitors(business_input)

    def _clean_domain(self, domain: str) -> str:
        """Clean and validate domain names"""
        if not domain:
            return ""
        
        domain = domain.lower()
        domain = domain.replace("https://", "").replace("http://", "")
        domain = domain.replace("www.", "")
        domain = domain.strip("/")
        
        return domain

    def _get_fallback_competitors(self, business_input: BusinessInput) -> List[CompetitorBasic]:
        """
        Provide fallback competitors based on common patterns
        """
        idea_lower = business_input.idea_description.lower()
        
        # Generic fallbacks
        return [
            CompetitorBasic(
                name="Unknown Competitor 1", 
                domain="", 
                type=CompetitorType.DIRECT,
                description="Competitor discovery failed"
            ),
            CompetitorBasic(
                name="Unknown Competitor 2", 
                domain="", 
                type=CompetitorType.INDIRECT,
                description="Competitor discovery failed"
            ),
            CompetitorBasic(
                name="Unknown Competitor 3", 
                domain="", 
                type=CompetitorType.SUBSTITUTE,
                description="Competitor discovery failed"
            )
        ]