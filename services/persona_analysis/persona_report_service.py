import asyncio
import json
from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from core.persona_models import (
    PersonaAnalysisInput, TargetPersona, PersonaReport
)
from config.settings import settings


class PersonaReportService:
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.openai_api_key,
            model=settings.llm_model,
            temperature=0.3
        )
        
        self.market_insights_prompt = ChatPromptTemplate.from_template("""
        Based on this persona analysis, generate 5 key market insights:
        
        Business Idea: {business_idea}
        Target Personas: {personas_summary}
        Social Media Data: {social_data}
        
        Provide insights about:
        1. Market size and opportunity
        2. Customer behavior patterns
        3. Competitive landscape from customer perspective
        4. Technology adoption trends
        5. Purchasing decision factors
        
        Return as JSON array of 5 insight strings:
        ["insight1", "insight2", "insight3", "insight4", "insight5"]
        """)
        
        self.targeting_recommendations_prompt = ChatPromptTemplate.from_template("""
        Generate targeting recommendations for these personas:
        
        Business Idea: {business_idea}
        Personas: {personas_data}
        Social Media Insights: {social_insights}
        
        Provide 5 specific targeting recommendations covering:
        1. Platform-specific targeting strategies
        2. Messaging and positioning approaches
        3. Content marketing strategies
        4. Channel optimization
        5. Budget allocation recommendations
        
        Return as JSON array of 5 recommendation strings:
        ["recommendation1", "recommendation2", ...]
        """)
        
        self.content_strategy_prompt = ChatPromptTemplate.from_template("""
        Create content strategy recommendations based on these personas:
        
        Business Idea: {business_idea}
        Personas: {personas_summary}
        Tech Habits: {tech_habits_summary}
        
        Provide 5 content strategy recommendations covering:
        1. Content types that resonate with each persona
        2. Platform-specific content approaches
        3. Content topics and themes
        4. Engagement tactics
        5. Content distribution strategy
        
        Return as JSON array of 5 strategy recommendations:
        ["strategy1", "strategy2", ...]
        """)

    async def generate_persona_report(
        self,
        analysis_input: PersonaAnalysisInput,
        personas: List[TargetPersona],
        social_media_data: Dict[str, Any],
        errors: List[str]
    ) -> PersonaReport:
        """
        Generate comprehensive persona analysis report
        """
        try:
            # Generate insights and recommendations in parallel
            tasks = [
                self._generate_market_insights(analysis_input, personas, social_media_data),
                self._generate_targeting_recommendations(analysis_input, personas, social_media_data),
                self._generate_content_strategy(analysis_input, personas)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle exceptions
            market_insights = results[0] if not isinstance(results[0], Exception) else self._fallback_market_insights()
            targeting_recs = results[1] if not isinstance(results[1], Exception) else self._fallback_targeting_recommendations()
            content_strategy = results[2] if not isinstance(results[2], Exception) else self._fallback_content_strategy()
            
            # Create the report
            report = PersonaReport(
                business_idea=analysis_input.business_idea,
                total_personas=len(personas),
                personas=personas,
                market_insights=market_insights,
                targeting_recommendations=targeting_recs,
                content_strategy_recommendations=content_strategy,
                execution_time=0.0  # Will be set by workflow
            )
            
            return report
            
        except Exception as e:
            print(f"Report generation failed: {e}")
            return self._generate_fallback_report(analysis_input, personas)

    async def _generate_market_insights(
        self,
        analysis_input: PersonaAnalysisInput,
        personas: List[TargetPersona],
        social_media_data: Dict[str, Any]
    ) -> List[str]:
        """
        Generate market insights using AI
        """
        try:
            # Prepare personas summary
            personas_summary = []
            for persona in personas:
                personas_summary.append({
                    "name": persona.name,
                    "demographics": persona.demographics.dict(),
                    "professional": persona.professional_details.dict(),
                    "pain_points": [pp.problem_description for pp in persona.pain_points_analysis],
                    "market_size": persona.persona_insights.market_size
                })
            
            chain = self.market_insights_prompt | self.llm | JsonOutputParser()
            
            result = await asyncio.to_thread(
                chain.invoke,
                {
                    "business_idea": analysis_input.business_idea,
                    "personas_summary": json.dumps(personas_summary, indent=2),
                    "social_data": json.dumps(social_media_data, indent=2)[:1500]
                }
            )
            
            # Normalize the output: extract insight string if it's a dict
            if isinstance(result, list):
                return [
                    item["insight"] if isinstance(item, dict) and "insight" in item else str(item)
                    for item in result
                ]
            
            return self._fallback_market_insights()
            
        except Exception as e:
            print(f"Market insights generation failed: {e}")
            return self._fallback_market_insights()

    async def _generate_targeting_recommendations(
        self,
        analysis_input: PersonaAnalysisInput,
        personas: List[TargetPersona],
        social_media_data: Dict[str, Any]
    ) -> List[str]:
        """
        Generate targeting recommendations using AI
        """
        try:
            # Prepare personas data for targeting analysis
            personas_data = []
            for persona in personas:
                personas_data.append({
                    "name": persona.name,
                    "platforms": persona.tech_habits.preferred_platforms,
                    "content_preferences": persona.tech_habits.content_consumption,
                    "professional_details": persona.professional_details.dict(),
                    "buying_behavior": persona.psychographics.buying_behavior
                })
            
            chain = self.targeting_recommendations_prompt | self.llm | JsonOutputParser()
            
            result = await asyncio.to_thread(
                chain.invoke,
                {
                    "business_idea": analysis_input.business_idea,
                    "personas_data": json.dumps(personas_data, indent=2),
                    "social_insights": json.dumps(social_media_data, indent=2)[:1500]
                }
            )
            
            # Normalize the output: extract recommendation string if it's a dict
            if isinstance(result, list):
                return [
                    item["recommendation"] if isinstance(item, dict) and "recommendation" in item else str(item)
                    for item in result
                ]
            
            return self._fallback_targeting_recommendations()
            
        except Exception as e:
            print(f"Targeting recommendations generation failed: {e}")
            return self._fallback_targeting_recommendations()

    async def _generate_content_strategy(
        self,
        analysis_input: PersonaAnalysisInput,
        personas: List[TargetPersona]
    ) -> List[str]:
        """
        Generate content strategy recommendations using AI
        """
        try:
            # Prepare content-focused persona summary
            personas_summary = []
            tech_habits_summary = []

            for persona in personas:
                personas_summary.append({
                    "name": persona.name,
                    "goals": persona.psychographics.goals,
                    "pain_points": [pp.problem_description for pp in persona.pain_points_analysis],
                    "motivations": persona.psychographics.motivations
                })

                tech_habits_summary.extend(persona.tech_habits.content_consumption)

            chain = self.content_strategy_prompt | self.llm | JsonOutputParser()

            result = await asyncio.to_thread(
                chain.invoke,
                {
                    "business_idea": analysis_input.business_idea,
                    "personas_summary": json.dumps(personas_summary, indent=2),
                    "tech_habits_summary": json.dumps(list(set(tech_habits_summary)), indent=2)
                }
            )

            # Normalize the output: extract strategy string if it's a dict
            if isinstance(result, list):
                return [
                    item["strategy"] if isinstance(item, dict) and "strategy" in item else str(item)
                    for item in result
                ]

            return self._fallback_content_strategy()

        except Exception as e:
            print(f"Content strategy generation failed: {e}")
            return self._fallback_content_strategy()


    def _fallback_market_insights(self) -> List[str]:
        """Generate fallback market insights"""
        return [
            "Target market shows strong demand for automated solutions",
            "Professional users prefer tools that integrate with existing workflows",
            "Mobile-first approach is critical for user adoption",
            "Price sensitivity varies significantly across different user segments",
            "Social proof and reviews heavily influence purchasing decisions"
        ]

    def _fallback_targeting_recommendations(self) -> List[str]:
        """Generate fallback targeting recommendations"""
        return [
            "Focus LinkedIn advertising on professional decision-makers",
            "Use content marketing to build trust and demonstrate expertise",
            "Implement retargeting campaigns for website visitors",
            "Leverage industry-specific communities and forums",
            "Create persona-specific landing pages for better conversion"
        ]

    def _fallback_content_strategy(self) -> List[str]:
        """Generate fallback content strategy"""
        return [
            "Create how-to content addressing specific pain points",
            "Develop case studies showcasing successful implementations",
            "Produce short-form video content for social media engagement",
            "Write industry-specific blog posts to attract organic traffic",
            "Design interactive tools and calculators for lead generation"
        ]

    def _generate_fallback_report(
        self,
        analysis_input: PersonaAnalysisInput,
        personas: List[TargetPersona]
    ) -> PersonaReport:
        """Generate fallback report when AI generation fails"""
        return PersonaReport(
            business_idea=analysis_input.business_idea,
            total_personas=len(personas),
            personas=personas,
            market_insights=self._fallback_market_insights(),
            targeting_recommendations=self._fallback_targeting_recommendations(),
            content_strategy_recommendations=self._fallback_content_strategy(),
            execution_time=0.0
        )