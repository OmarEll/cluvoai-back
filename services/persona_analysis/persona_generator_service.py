# persona_generator_service.py

import asyncio
import json
from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from core.persona_models import (
    PersonaAnalysisInput, TargetPersona, PersonaDemographic, 
    ProfessionalDetails, PersonaPsychographics, TechHabits,
    PersonaInsights, PainPointAnalysis
)
from config.settings import settings


class PersonaGeneratorService:
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.openai_api_key,
            model=settings.llm_model,
            temperature=0.4
        )

        self.persona_generation_prompt = ChatPromptTemplate.from_template("""
        Generate 3 detailed target personas based on the business idea, social media research, and competitor insights:
        
        **BUSINESS CONTEXT:**
        Business Idea: {business_idea}
        Target Market: {target_market}
        Industry: {industry}

        **SOCIAL MEDIA RESEARCH:**
        {social_media_data}

        **COMPETITOR ANALYSIS CONTEXT:**
        {competitor_context}

        **PERSONA REQUIREMENTS:**
        Generate 3 distinct, data-driven personas that:
        1. Leverage competitor insights to identify real user behaviors and pain points
        2. Address gaps in competitor targeting approaches
        3. Reflect actual market segments based on competitor analysis
        4. Consider user feedback patterns from competitor research

        For each persona, provide:
        1. A descriptive name that reflects their key characteristic
        2. Demographics (age range, gender, location, income range)
        3. Professional details (job title, industry, company size, experience level)
        4. Psychographics (goals, pain points, motivations, buying behavior)
        5. Tech habits (preferred platforms, devices, software tools, content consumption)
        6. Persona insights (market size estimate, how competitors target them, identified gaps, engagement opportunities)

        **IMPORTANT:** If competitor context is available, prioritize insights from real user data over generic assumptions.
        Focus on underserved segments and differentiation opportunities identified in the competitor analysis.

        Return as JSON array with 3 persona objects following the exact structure expected.
        """)

        self.pain_point_analysis_prompt = ChatPromptTemplate.from_template("""
        Analyze the pain points for this persona and business context:

        Persona: {persona_name}
        Business Idea: {business_idea}
        Persona Details: {persona_data}
        Social Media Insights: {social_insights}

        Identify 3-5 specific pain points and for each provide:
        1. Problem description
        2. Frequency
        3. Severity (1-10)
        4. Current solutions used
        5. Value proposition opportunity

        Return as JSON array.
        """)

    async def generate_personas(
        self, 
        analysis_input: PersonaAnalysisInput, 
        social_media_data: Dict[str, Any],
        competitor_context: str = ""
    ) -> List[TargetPersona]:
        print("👥 Generating target personas...")
        try:
            personas_data = await self._generate_base_personas(analysis_input, social_media_data, competitor_context)
            enhanced_personas = []
            for persona_data in personas_data:
                enhanced_persona = await self._enhance_persona_with_pain_points(
                    persona_data, analysis_input, social_media_data
                )
                enhanced_personas.append(enhanced_persona)
            print(f"✅ Generated {len(enhanced_personas)} detailed personas")
            return enhanced_personas
        except Exception as e:
            print(f"Persona generation failed: {e}")
            return self._generate_fallback_personas(analysis_input)

    async def _generate_base_personas(self, analysis_input: PersonaAnalysisInput, social_media_data: Dict[str, Any], competitor_context: str = "") -> List[Dict[str, Any]]:
        chain = self.persona_generation_prompt | self.llm | JsonOutputParser()
        result = await asyncio.to_thread(
            chain.invoke,
            {
                "business_idea": analysis_input.business_idea,
                "target_market": analysis_input.target_market or "General business market",
                "industry": analysis_input.industry or "Technology",
                "social_media_data": json.dumps(social_media_data, indent=2)[:2000],
                "competitor_context": competitor_context or "No competitor analysis data available."
            }
        )
        return result if isinstance(result, list) else [result]

    async def _enhance_persona_with_pain_points(self, persona_data: Dict[str, Any], analysis_input: PersonaAnalysisInput, social_media_data: Dict[str, Any]) -> TargetPersona:
        try:
            chain = self.pain_point_analysis_prompt | self.llm | JsonOutputParser()
            pain_points_result = await asyncio.to_thread(
                chain.invoke,
                {
                    "persona_name": persona_data.get("name", "Unknown Persona"),
                    "business_idea": analysis_input.business_idea,
                    "persona_data": json.dumps(persona_data, indent=2),
                    "social_insights": json.dumps(social_media_data, indent=2)[:1000]
                }
            )
            pain_point_analyses = [PainPointAnalysis(**pp) for pp in pain_points_result if isinstance(pp, dict)]
        except Exception as e:
            print(f"Pain point analysis failed for {persona_data.get('name', 'Unknown')}: {e}")
            pain_point_analyses = self._generate_fallback_pain_points(analysis_input)

        # Normalize psychographics
        psychographics_data = persona_data.get("psychographics", {})
        if isinstance(psychographics_data.get("buying_behavior"), str):
            psychographics_data["buying_behavior"] = [
                x.strip() for x in psychographics_data["buying_behavior"].split(",")
            ]
        psychographics = PersonaPsychographics(**psychographics_data)

        # Normalize persona insights fields
        insights_data = persona_data.get("persona_insights", {})
        for key in ["competitor_targeting", "gaps_identified", "engagement_opportunities"]:
            if isinstance(insights_data.get(key), str):
                insights_data[key] = [
                    x.strip() for x in insights_data[key].split(",") if x.strip()
                ]
        persona_insights = PersonaInsights(**insights_data)

        try:
            return TargetPersona(
                name=persona_data.get("name", "Unknown Persona"),
                description=persona_data.get("description", ""),
                demographics=PersonaDemographic(**persona_data.get("demographics", {})),
                professional_details=ProfessionalDetails(**persona_data.get("professional_details", {})),
                psychographics=psychographics,
                tech_habits=TechHabits(**persona_data.get("tech_habits", {})),
                pain_points_analysis=pain_point_analyses,
                persona_insights=persona_insights,
                confidence_score=0.8
            )
        except Exception as e:
            print(f"Persona object creation failed: {e}")
            return self._create_fallback_persona(persona_data.get("name", "Fallback Persona"), analysis_input)

    def _generate_fallback_personas(self, analysis_input: PersonaAnalysisInput) -> List[TargetPersona]:
        return [
            self._create_hr_manager_persona(),
            self._create_small_business_owner_persona(),
            self._create_talent_specialist_persona()
        ]

    def _create_fallback_persona(self, name: str, analysis_input: PersonaAnalysisInput) -> TargetPersona:
        return TargetPersona(
            name=name,
            description=f"Professional interested in {analysis_input.business_idea}",
            demographics=PersonaDemographic(
                age_range="25-45",
                gender="Mixed",
                location="Urban areas",
                income_range="$50,000-$100,000"
            ),
            professional_details=ProfessionalDetails(
                job_title="Manager",
                industry=analysis_input.industry or "Technology",
                company_size="10-500 employees",
                experience_level="3-10 years"
            ),
            psychographics=PersonaPsychographics(
                goals=["Improve efficiency", "Solve business problems"],
                pain_points=["Time constraints", "Manual processes"],
                motivations=["Professional growth", "Better outcomes"],
                buying_behavior=["Research thoroughly", "Compare options"]
            ),
            tech_habits=TechHabits(
                preferred_platforms=["LinkedIn", "Google"],
                device_usage=["Laptop", "Mobile"],
                software_tools=["Email", "Office suite"],
                content_consumption=["Articles", "Videos"]
            ),
            pain_points_analysis=self._generate_fallback_pain_points(analysis_input),
            persona_insights=PersonaInsights(
                market_size="Large addressable market",
                competitor_targeting=["Online advertising", "Content marketing"],
                gaps_identified=["Affordable solutions", "Easy implementation"],
                engagement_opportunities=["Professional networks", "Industry events"]
            ),
            confidence_score=0.5
        )

    def _generate_fallback_pain_points(self, analysis_input: PersonaAnalysisInput) -> List[PainPointAnalysis]:
        return [
            PainPointAnalysis(
                problem_description="Time-consuming manual processes",
                frequency="Daily",
                severity=7,
                current_solutions=["Manual work", "Basic tools"],
                value_proposition_opportunity="Automation and AI to reduce time by 70%"
            ),
            PainPointAnalysis(
                problem_description="Lack of data-driven insights",
                frequency="Weekly",
                severity=6,
                current_solutions=["Spreadsheets", "Basic reporting"],
                value_proposition_opportunity="AI-powered recommendations"
            ),
            PainPointAnalysis(
                problem_description="Difficulty finding affordable solutions",
                frequency="When purchasing",
                severity=8,
                current_solutions=["Expensive enterprise tools", "Free basic tools"],
                value_proposition_opportunity="Cost-effective solution with enterprise features"
            )
        ]

    def _create_hr_manager_persona(self) -> TargetPersona:
        return TargetPersona(
            name="Progressive HR Manager",
            description="Modern HR professional seeking efficient recruitment solutions",
            demographics=PersonaDemographic(
                age_range="28-42",
                gender="Mixed (60% female)",
                location="Urban areas, US/Europe",
                income_range="$60,000-$95,000"
            ),
            professional_details=ProfessionalDetails(
                job_title="HR Manager",
                industry="Technology/Professional Services",
                company_size="50-300 employees",
                experience_level="5-12 years"
            ),
            psychographics=PersonaPsychographics(
                goals=["Streamline hiring", "Improve candidate experience", "Reduce time-to-hire"],
                pain_points=["Manual resume screening", "Scheduling interviews", "Finding quality candidates"],
                motivations=["Efficiency", "Employee satisfaction", "Business impact"],
                buying_behavior=["Research online", "Read reviews", "Request demos"]
            ),
            tech_habits=TechHabits(
                preferred_platforms=["LinkedIn", "HR forums"],
                device_usage=["Laptop", "Mobile"],
                software_tools=["ATS", "HRIS"],
                content_consumption=["HR blogs", "Case studies"]
            ),
            pain_points_analysis=self._generate_fallback_pain_points(PersonaAnalysisInput(business_idea="HR Automation")),
            persona_insights=PersonaInsights(
                market_size="500,000+ HR professionals",
                competitor_targeting=["LinkedIn ads", "Conferences"],
                gaps_identified=["Affordable AI"],
                engagement_opportunities=["HR communities"]
            ),
            confidence_score=0.7
        )

    def _create_small_business_owner_persona(self) -> TargetPersona:
        return TargetPersona(
            name="Growth-Oriented Business Owner",
            description="Small business owner looking to scale hiring processes",
            demographics=PersonaDemographic(
                age_range="35-55",
                gender="Mixed (55% male)",
                location="US and Canada",
                income_range="$75,000-$150,000"
            ),
            professional_details=ProfessionalDetails(
                job_title="CEO/Founder/Owner",
                industry="Services/Tech",
                company_size="10-50 employees",
                experience_level="10-20 years"
            ),
            psychographics=PersonaPsychographics(
                goals=["Scale business", "Hire right people"],
                pain_points=["Limited HR resources", "Wearing many hats"],
                motivations=["Growth", "ROI"],
                buying_behavior=["Price-conscious", "Quick decisions"]
            ),
            tech_habits=TechHabits(
                preferred_platforms=["LinkedIn", "Facebook"],
                device_usage=["Mobile-heavy"],
                software_tools=["Cloud-based solutions"],
                content_consumption=["Success stories"]
            ),
            pain_points_analysis=self._generate_fallback_pain_points(PersonaAnalysisInput(business_idea="HR Automation")),
            persona_insights=PersonaInsights(
                market_size="6M+ small businesses",
                competitor_targeting=["Google ads"],
                gaps_identified=["Simple pricing"],
                engagement_opportunities=["Local communities"]
            ),
            confidence_score=0.7
        )

    def _create_talent_specialist_persona(self) -> TargetPersona:
        return TargetPersona(
            name="Tech-Savvy Talent Specialist",
            description="Recruitment specialist focused on efficiency and scale",
            demographics=PersonaDemographic(
                age_range="24-38",
                gender="Mixed (65% female)",
                location="Urban metro areas",
                income_range="$45,000-$75,000"
            ),
            professional_details=ProfessionalDetails(
                job_title="Talent Acquisition Specialist",
                industry="Staffing/Tech",
                company_size="100-1000 employees",
                experience_level="2-8 years"
            ),
            psychographics=PersonaPsychographics(
                goals=["Fill positions fast", "Improve hiring KPIs"],
                pain_points=["High volume screening", "Ghosting"],
                motivations=["Career growth", "Tech efficiency"],
                buying_behavior=["Feature-focused", "Free trials"]
            ),
            tech_habits=TechHabits(
                preferred_platforms=["LinkedIn", "Glassdoor"],
                device_usage=["Laptop", "Mobile"],
                software_tools=["ATS", "CRM"],
                content_consumption=["Podcasts", "LinkedIn posts"]
            ),
            pain_points_analysis=self._generate_fallback_pain_points(PersonaAnalysisInput(business_idea="Recruitment Automation")),
            persona_insights=PersonaInsights(
                market_size="200K+ professionals",
                competitor_targeting=["Conferences", "LinkedIn"],
                gaps_identified=["AI automation"],
                engagement_opportunities=["Recruiter communities"]
            ),
            confidence_score=0.7
        )