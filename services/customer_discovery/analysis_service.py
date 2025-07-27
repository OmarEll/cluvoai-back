import asyncio
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import uuid

from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from langchain.prompts import ChatPromptTemplate

from core.customer_discovery_models import (
    InterviewAnalysis, ExtractedInsight, InterviewScore, CustomerInterview,
    Transcription, InsightType, ConfidenceLevel, ScoreCategory, CustomerSegment
)
from config.settings import settings


class CustomerDiscoveryAnalysisService:
    """
    AI-powered service for analyzing customer discovery interviews
    Extracts insights, pain points, validation data, and provides objective scoring
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            openai_api_key=settings.openai_api_key,
            temperature=0.1  # Low temperature for consistent analysis
        )
        self.parser = JsonOutputParser()
        
        # Create comprehensive analysis prompt
        self.analysis_prompt = ChatPromptTemplate.from_template("""
        You are an expert customer discovery analyst specializing in extracting actionable business insights from customer interviews.
        
        Your task is to analyze the following customer interview transcript and extract key insights with objective scoring.
        
        INTERVIEW CONTEXT:
        Business Idea: {business_idea}
        Customer Profile: {customer_profile}
        Interview Type: {interview_type}
        
        TRANSCRIPT:
        {transcript}
        
        ANALYSIS REQUIREMENTS:
        
        1. **PAIN POINTS EXTRACTION**
        - Identify specific customer pain points
        - Rate severity (1-10) based on frequency of mention and emotional language
        - Extract exact quotes that demonstrate the pain
        
        2. **VALIDATION POINTS EXTRACTION**
        - Identify statements that validate or invalidate the business idea
        - Note willingness to pay indicators
        - Extract solution interest signals
        
        3. **INSIGHT CATEGORIZATION**
        Extract insights for each category:
        - pain_point: Customer problems and frustrations
        - validation_point: Evidence supporting/refuting the business idea
        - feature_request: Specific features or capabilities requested
        - pricing_feedback: Comments about pricing, budget, or value
        - competitive_mention: References to existing solutions or competitors
        - market_size_indicator: Clues about market size or target audience
        - persona_characteristic: Traits that define customer segments
        - bmc_update: Information that should update the Business Model Canvas
        
        4. **OBJECTIVE SCORING** (1-10 scale):
        - problem_confirmation: How strongly does the customer confirm the problem exists?
        - solution_interest: How interested are they in the proposed solution?
        - willingness_to_pay: Likelihood they would pay for this solution
        - urgency: How urgent is solving this problem for them?
        - frequency: How often do they experience this problem?
        - intensity: How much does this problem impact them?
        - market_size: How representative is this customer of a larger market?
        - competitive_advantage: How much better is this solution vs alternatives?
        
        5. **CONFIDENCE ASSESSMENT**
        Rate confidence (low/medium/high/very_high) based on:
        - Clarity of customer statements
        - Consistency throughout interview
        - Specific examples provided
        - Emotional investment in responses
        
        6. **BMC IMPACT ANALYSIS**
        Identify which Business Model Canvas sections should be updated:
        - customer_segments: New segment characteristics
        - value_propositions: Refined value props based on feedback
        - channels: Preferred customer touchpoints mentioned
        - customer_relationships: Relationship preferences
        - revenue_streams: Pricing model feedback
        - key_resources: Resources needed based on customer needs
        - key_activities: Activities emphasized by customers
        - key_partnerships: Partner suggestions from customers
        - cost_structure: Cost considerations from customer perspective
        
        7. **SENTIMENT ANALYSIS**
        Analyze overall sentiment:
        - enthusiasm_level: Customer excitement about the solution (0-1)
        - frustration_level: Current problem frustration (0-1)
        - skepticism_level: Doubt about proposed solution (0-1)
        
        8. **FOLLOW-UP RECOMMENDATIONS**
        Suggest specific follow-up questions and next steps based on gaps in information.
        
        Return your analysis as JSON with the following structure:
        {{
            "overall_score": float,
            "category_scores": [
                {{
                    "category": "problem_confirmation",
                    "score": float,
                    "reasoning": "string",
                    "supporting_quotes": ["quote1", "quote2"]
                }}
            ],
            "extracted_insights": [
                {{
                    "type": "pain_point",
                    "content": "summary of insight",
                    "quote": "exact customer quote",
                    "context": "surrounding context",
                    "confidence": "high",
                    "confidence_score": 0.85,
                    "impact_score": 8.5,
                    "tags": ["tag1", "tag2"],
                    "bmc_impact": {{
                        "sections": ["value_propositions"],
                        "updates": {{"specific": "changes"}}
                    }}
                }}
            ],
            "pain_points": ["pain1", "pain2"],
            "validation_points": ["validation1", "validation2"],
            "feature_requests": ["feature1", "feature2"],
            "competitive_mentions": ["competitor1", "competitor2"],
            "pricing_feedback": ["price feedback1", "price feedback2"],
            "persona_updates": {{
                "characteristics": ["trait1", "trait2"],
                "goals": ["goal1", "goal2"],
                "pain_points": ["pain1", "pain2"]
            }},
            "bmc_updates": {{
                "customer_segments": {{"updates": "specific changes"}},
                "value_propositions": {{"updates": "specific changes"}}
            }},
            "follow_up_questions": ["question1", "question2"],
            "next_steps": ["step1", "step2"],
            "sentiment_analysis": {{
                "enthusiasm_level": 0.7,
                "frustration_level": 0.8,
                "skepticism_level": 0.3
            }}
        }}
        
        Be objective, data-driven, and specific in your analysis. Base all scores on concrete evidence from the transcript.
        """)
        
        # Create insight extraction prompt for focused analysis
        self.insight_extraction_prompt = ChatPromptTemplate.from_template("""
        You are analyzing a customer interview transcript to extract specific insights.
        
        TRANSCRIPT SECTION:
        {transcript_section}
        
        BUSINESS CONTEXT:
        {business_context}
        
        Extract insights of type: {insight_type}
        
        For each insight found, provide:
        1. The exact quote from the customer
        2. Your interpretation/summary
        3. Confidence level (low/medium/high/very_high)
        4. Impact score (1-10) on business decisions
        5. Relevant tags for categorization
        
        Return as JSON array of insights.
        """)
    
    async def analyze_interview(
        self,
        interview: CustomerInterview,
        transcription: Transcription,
        business_context: Optional[Dict[str, Any]] = None
    ) -> InterviewAnalysis:
        """
        Perform comprehensive analysis of a customer interview
        """
        try:
            print(f"🧠 Starting comprehensive interview analysis for interview: {interview.id}")
            start_time = datetime.utcnow()
            
            # Prepare context for analysis
            business_idea = business_context.get("business_idea", "Unknown") if business_context else "Unknown"
            customer_profile = interview.customer_profile.dict()
            interview_type = interview.interview_type
            transcript = transcription.content
            
            # Run AI analysis
            analysis_result = await self._run_comprehensive_analysis(
                business_idea, customer_profile, interview_type, transcript
            )
            
            # Create analysis object
            analysis_id = str(uuid.uuid4())
            
            # Process extracted insights
            insights = []
            for insight_data in analysis_result.get("extracted_insights", []):
                insight = ExtractedInsight(
                    id=str(uuid.uuid4()),
                    interview_id=interview.id,
                    type=InsightType(insight_data.get("type", "pain_point")),
                    content=insight_data.get("content", ""),
                    quote=insight_data.get("quote", ""),
                    context=insight_data.get("context", ""),
                    confidence=ConfidenceLevel(insight_data.get("confidence", "medium")),
                    confidence_score=insight_data.get("confidence_score", 0.5),
                    impact_score=insight_data.get("impact_score", 5.0),
                    tags=insight_data.get("tags", []),
                    bmc_impact=insight_data.get("bmc_impact"),
                    created_at=datetime.utcnow()
                )
                insights.append(insight)
            
            # Process category scores
            category_scores = []
            for score_data in analysis_result.get("category_scores", []):
                score = InterviewScore(
                    category=ScoreCategory(score_data.get("category")),
                    score=score_data.get("score", 5.0),
                    reasoning=score_data.get("reasoning", ""),
                    supporting_quotes=score_data.get("supporting_quotes", []),
                    confidence=self._determine_confidence_from_score(score_data.get("score", 5.0))
                )
                category_scores.append(score)
            
            # Create complete analysis
            analysis = InterviewAnalysis(
                id=analysis_id,
                interview_id=interview.id,
                overall_score=analysis_result.get("overall_score", 5.0),
                category_scores=category_scores,
                key_insights=insights,
                pain_points=analysis_result.get("pain_points", []),
                validation_points=analysis_result.get("validation_points", []),
                feature_requests=analysis_result.get("feature_requests", []),
                competitive_mentions=analysis_result.get("competitive_mentions", []),
                pricing_feedback=analysis_result.get("pricing_feedback", []),
                persona_updates=analysis_result.get("persona_updates", {}),
                bmc_updates=analysis_result.get("bmc_updates", {}),
                follow_up_questions=analysis_result.get("follow_up_questions", []),
                next_steps=analysis_result.get("next_steps", []),
                sentiment_analysis=analysis_result.get("sentiment_analysis", {}),
                created_at=datetime.utcnow()
            )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            print(f"✅ Interview analysis completed in {processing_time:.2f} seconds")
            print(f"   Overall score: {analysis.overall_score}/10")
            print(f"   Insights extracted: {len(insights)}")
            print(f"   Pain points: {len(analysis.pain_points)}")
            print(f"   Validation points: {len(analysis.validation_points)}")
            
            return analysis
            
        except Exception as e:
            print(f"❌ Interview analysis failed: {e}")
            raise Exception(f"Failed to analyze interview: {str(e)}")
    
    async def extract_specific_insights(
        self,
        transcript: str,
        insight_type: InsightType,
        business_context: Dict[str, Any]
    ) -> List[ExtractedInsight]:
        """
        Extract specific types of insights from transcript
        """
        try:
            print(f"🔍 Extracting {insight_type} insights from transcript")
            
            # Split transcript into manageable sections
            sections = self._split_transcript(transcript)
            all_insights = []
            
            for section in sections:
                # Extract insights from this section
                insights_data = await self._extract_insights_from_section(
                    section, insight_type, business_context
                )
                
                # Create insight objects
                for insight_data in insights_data:
                    insight = ExtractedInsight(
                        id=str(uuid.uuid4()),
                        interview_id="",  # Will be set by caller
                        type=insight_type,
                        content=insight_data.get("content", ""),
                        quote=insight_data.get("quote", ""),
                        context=insight_data.get("context", ""),
                        confidence=ConfidenceLevel(insight_data.get("confidence", "medium")),
                        confidence_score=insight_data.get("confidence_score", 0.5),
                        impact_score=insight_data.get("impact_score", 5.0),
                        tags=insight_data.get("tags", []),
                        created_at=datetime.utcnow()
                    )
                    all_insights.append(insight)
            
            print(f"✅ Extracted {len(all_insights)} {insight_type} insights")
            return all_insights
            
        except Exception as e:
            print(f"❌ Insight extraction failed: {e}")
            return []
    
    async def calculate_segment_scores(
        self,
        interviews: List[CustomerInterview],
        segment: CustomerSegment
    ) -> Dict[str, float]:
        """
        Calculate aggregated scores for a customer segment
        """
        try:
            print(f"📊 Calculating scores for segment: {segment}")
            
            segment_interviews = [
                interview for interview in interviews
                if interview.customer_profile.segment == segment
            ]
            
            if not segment_interviews:
                return {}
            
            # Aggregate scores across all interviews in segment
            aggregated_scores = {}
            score_categories = list(ScoreCategory)
            
            for category in score_categories:
                category_scores = []
                
                for interview in segment_interviews:
                    if interview.analysis and interview.analysis.category_scores:
                        for score in interview.analysis.category_scores:
                            if score.category == category:
                                category_scores.append(score.score)
                
                if category_scores:
                    aggregated_scores[category.value] = sum(category_scores) / len(category_scores)
                else:
                    aggregated_scores[category.value] = 0.0
            
            # Calculate overall segment score
            if aggregated_scores:
                overall_score = sum(aggregated_scores.values()) / len(aggregated_scores)
                aggregated_scores["overall"] = overall_score
            
            print(f"✅ Segment scores calculated: {len(aggregated_scores)} categories")
            return aggregated_scores
            
        except Exception as e:
            print(f"❌ Segment score calculation failed: {e}")
            return {}
    
    async def _run_comprehensive_analysis(
        self,
        business_idea: str,
        customer_profile: Dict[str, Any],
        interview_type: str,
        transcript: str
    ) -> Dict[str, Any]:
        """
        Run the comprehensive AI analysis
        """
        try:
            # Prepare the prompt
            formatted_prompt = self.analysis_prompt.format(
                business_idea=business_idea,
                customer_profile=json.dumps(customer_profile, indent=2),
                interview_type=interview_type,
                transcript=transcript
            )
            
            # Get AI analysis
            response = await self.llm.ainvoke(formatted_prompt)
            
            # Parse JSON response
            try:
                analysis_result = json.loads(response.content)
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract JSON from response
                analysis_result = self._extract_json_from_response(response.content)
            
            return analysis_result
            
        except Exception as e:
            print(f"Error in comprehensive analysis: {e}")
            return self._create_fallback_analysis()
    
    async def _extract_insights_from_section(
        self,
        transcript_section: str,
        insight_type: InsightType,
        business_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Extract insights from a specific transcript section
        """
        try:
            formatted_prompt = self.insight_extraction_prompt.format(
                transcript_section=transcript_section,
                business_context=json.dumps(business_context, indent=2),
                insight_type=insight_type.value
            )
            
            response = await self.llm.ainvoke(formatted_prompt)
            
            try:
                insights = json.loads(response.content)
                return insights if isinstance(insights, list) else []
            except json.JSONDecodeError:
                return []
                
        except Exception as e:
            print(f"Error extracting insights from section: {e}")
            return []
    
    def _split_transcript(self, transcript: str, max_length: int = 3000) -> List[str]:
        """
        Split transcript into manageable sections for analysis
        """
        sections = []
        words = transcript.split()
        current_section = []
        current_length = 0
        
        for word in words:
            current_section.append(word)
            current_length += len(word) + 1
            
            if current_length >= max_length:
                sections.append(" ".join(current_section))
                current_section = []
                current_length = 0
        
        if current_section:
            sections.append(" ".join(current_section))
        
        return sections
    
    def _determine_confidence_from_score(self, score: float) -> ConfidenceLevel:
        """
        Determine confidence level based on score
        """
        if score >= 8.5:
            return ConfidenceLevel.VERY_HIGH
        elif score >= 7.0:
            return ConfidenceLevel.HIGH
        elif score >= 5.0:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def _extract_json_from_response(self, response_text: str) -> Dict[str, Any]:
        """
        Extract JSON from AI response if it's not properly formatted
        """
        try:
            # Try to find JSON-like content in the response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_content = response_text[json_start:json_end]
                return json.loads(json_content)
            
            return self._create_fallback_analysis()
            
        except Exception:
            return self._create_fallback_analysis()
    
    def _create_fallback_analysis(self) -> Dict[str, Any]:
        """
        Create a fallback analysis when AI analysis fails
        """
        return {
            "overall_score": 5.0,
            "category_scores": [
                {
                    "category": "problem_confirmation",
                    "score": 5.0,
                    "reasoning": "Analysis unavailable",
                    "supporting_quotes": []
                }
            ],
            "extracted_insights": [],
            "pain_points": [],
            "validation_points": [],
            "feature_requests": [],
            "competitive_mentions": [],
            "pricing_feedback": [],
            "persona_updates": {},
            "bmc_updates": {},
            "follow_up_questions": [],
            "next_steps": [],
            "sentiment_analysis": {
                "enthusiasm_level": 0.5,
                "frustration_level": 0.5,
                "skepticism_level": 0.5
            }
        }


# Create singleton instance
analysis_service = CustomerDiscoveryAnalysisService() 