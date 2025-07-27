import asyncio
import aiohttp
import json
from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from core.persona_models import PersonaAnalysisInput
from config.settings import settings


class SocialMediaAnalysisService:
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.openai_api_key,
            model=settings.llm_model,
            temperature=0.3
        )
        
        self.keyword_discovery_prompt = ChatPromptTemplate.from_template("""
        For this business idea: "{business_idea}"
        Target market: {target_market}
        Industry: {industry}
        
        Generate comprehensive keyword research for social media analysis:
        
        1. PRIMARY KEYWORDS (5-8 main terms people would use)
        2. SECONDARY KEYWORDS (10-15 related terms)
        3. HASHTAGS (15-20 relevant hashtags for Twitter/Instagram)
        4. PROBLEM KEYWORDS (terms people use when expressing pain points)
        5. SOLUTION KEYWORDS (terms people use when seeking solutions)
        
        Return as JSON:
        {{
            "primary_keywords": ["keyword1", "keyword2", ...],
            "secondary_keywords": ["keyword1", "keyword2", ...],
            "hashtags": ["#hashtag1", "#hashtag2", ...],
            "problem_keywords": ["problem1", "problem2", ...],
            "solution_keywords": ["solution1", "solution2", ...]
        }}
        """)
        
        self.subreddit_discovery_prompt = ChatPromptTemplate.from_template("""
        For this business idea: "{business_idea}"
        Target market: {target_market}
        Industry: {industry}
        
        Identify 15-20 relevant Reddit communities where potential customers would be active.
        Consider:
        - Industry-specific subreddits
        - Problem-focused communities
        - Target demographic subreddits
        - Professional communities
        - Hobby/interest communities related to the target market
        - General business communities
        
        Return as JSON array of subreddit names (without r/):
        ["subreddit1", "subreddit2", "subreddit3", ...]
        
        Examples for reference:
        - For a fitness app: ["fitness", "loseit", "bodyweightfitness", "nutrition", "running"]
        - For a finance tool: ["personalfinance", "investing", "entrepreneur", "smallbusiness", "financialplanning"]
        """)
        
        self.social_insights_prompt = ChatPromptTemplate.from_template("""
        Based on this social media research for: "{business_idea}"
        
        Keywords found: {keywords}
        Communities analyzed: {communities}
        Target market: {target_market}
        
        Analyze and extract key insights about the target audience:
        
        1. DEMOGRAPHIC PATTERNS (age, gender, location, income)
        2. BEHAVIORAL PATTERNS (online habits, content preferences, engagement style)
        3. PAIN POINTS (problems they discuss, frustrations they express)
        4. GOALS & MOTIVATIONS (what they're trying to achieve)
        5. LANGUAGE & TONE (how they communicate, terminology they use)
        6. PLATFORM PREFERENCES (which social platforms they prefer and why)
        7. CONTENT CONSUMPTION (types of content they engage with most)
        8. PURCHASE BEHAVIOR (how they research and make buying decisions)
        
        Return comprehensive insights as JSON:
        {{
            "demographics": {{
                "age_ranges": ["25-35", "36-45"],
                "gender_distribution": "Mixed with slight female majority",
                "locations": ["Urban areas", "Suburbs"],
                "income_levels": ["$50k-$80k", "$80k-$120k"]
            }},
            "behavioral_patterns": {{
                "online_activity": ["Active on weekday evenings", "Weekend browsing"],
                "content_preferences": ["Video content", "How-to guides"],
                "engagement_style": ["Asks questions", "Shares experiences"]
            }},
            "pain_points": ["specific pain point 1", "specific pain point 2"],
            "goals_motivations": ["goal 1", "goal 2"],
            "communication_style": {{
                "tone": "Professional but casual",
                "terminology": ["term1", "term2"],
                "common_phrases": ["phrase1", "phrase2"]
            }},
            "platform_preferences": {{
                "primary": ["LinkedIn", "Reddit"],
                "secondary": ["Twitter", "YouTube"],
                "usage_context": "Professional networking and problem-solving"
            }},
            "content_consumption": {{
                "preferred_formats": ["Articles", "Short videos", "Infographics"],
                "topics_of_interest": ["Industry trends", "How-to content"],
                "engagement_triggers": ["Practical tips", "Real examples"]
            }},
            "purchase_behavior": {{
                "research_methods": ["Google search", "Peer recommendations"],
                "decision_factors": ["Price", "Features", "Reviews"],
                "buying_journey": ["Awareness", "Research", "Trial", "Purchase"]
            }}
        }}
        """)

    async def analyze_social_platforms(self, analysis_input: PersonaAnalysisInput) -> Dict[str, Any]:
        """
        Analyze social media platforms for persona insights - completely AI-driven
        """
        print("📱 Discovering keywords and communities...")
        
        # Step 1: AI-powered keyword discovery
        keywords = await self._discover_keywords(analysis_input)
        print(f"✅ Discovered {len(keywords.get('primary_keywords', []))} primary keywords")
        
        # Step 2: AI-powered subreddit discovery
        subreddits = await self._discover_subreddits(analysis_input)
        print(f"✅ Identified {len(subreddits)} relevant communities")
        
        # Step 3: Simulate social media research (in production, would use actual APIs)
        social_research_data = await self._simulate_social_research(keywords, subreddits, analysis_input)
        
        # Step 4: AI analysis of social insights
        social_insights = await self._analyze_social_insights(
            analysis_input, keywords, subreddits, social_research_data
        )
        
        print("✅ Social media analysis completed")
        
        return {
            "keywords": keywords,
            "relevant_communities": subreddits,
            "social_research": social_research_data,
            "insights": social_insights
        }

    async def _discover_keywords(self, analysis_input: PersonaAnalysisInput) -> Dict[str, List[str]]:
        """
        AI-powered keyword discovery for any business idea
        """
        try:
            chain = self.keyword_discovery_prompt | self.llm | JsonOutputParser()
            
            result = await asyncio.to_thread(
                chain.invoke,
                {
                    "business_idea": analysis_input.business_idea,
                    "target_market": analysis_input.target_market or "General market",
                    "industry": analysis_input.industry or "Technology"
                }
            )
            
            return result if isinstance(result, dict) else self._fallback_keywords(analysis_input)
            
        except Exception as e:
            print(f"Keyword discovery failed: {e}")
            return self._fallback_keywords(analysis_input)

    async def _discover_subreddits(self, analysis_input: PersonaAnalysisInput) -> List[str]:
        """
        AI-powered subreddit discovery for any business idea
        """
        try:
            chain = self.subreddit_discovery_prompt | self.llm | JsonOutputParser()
            
            result = await asyncio.to_thread(
                chain.invoke,
                {
                    "business_idea": analysis_input.business_idea,
                    "target_market": analysis_input.target_market or "General market",
                    "industry": analysis_input.industry or "Technology"
                }
            )
            
            return result if isinstance(result, list) else self._fallback_subreddits(analysis_input)
            
        except Exception as e:
            print(f"Subreddit discovery failed: {e}")
            return self._fallback_subreddits(analysis_input)

    async def _simulate_social_research(
        self, 
        keywords: Dict[str, List[str]], 
        subreddits: List[str], 
        analysis_input: PersonaAnalysisInput
    ) -> Dict[str, Any]:
        """
        Simulate social media research (replace with real API calls in production)
        """
        # This simulates what would be real social media API data
        return {
            "reddit_analysis": {
                "communities_analyzed": subreddits[:10],
                "total_posts_analyzed": 500,
                "common_discussion_topics": [
                    "Best practices and recommendations",
                    "Problem-solving discussions",
                    "Tool and service comparisons",
                    "Industry trends and news",
                    "Personal experiences and reviews"
                ],
                "user_activity_patterns": {
                    "peak_posting_times": ["9-11 AM", "1-3 PM", "7-9 PM"],
                    "most_active_days": ["Tuesday", "Wednesday", "Thursday"],
                    "engagement_types": ["Questions", "Advice-seeking", "Experience sharing"]
                }
            },
            "twitter_analysis": {
                "hashtags_analyzed": keywords.get("hashtags", [])[:15],
                "tweet_volume": "2.5k tweets/day average",
                "sentiment_distribution": {
                    "positive": "45%",
                    "neutral": "35%", 
                    "negative": "20%"
                },
                "conversation_themes": [
                    "Industry insights and trends",
                    "Product recommendations",
                    "Problem discussions",
                    "Success stories",
                    "Company announcements"
                ]
            },
            "linkedin_analysis": {
                "professional_discussions": True,
                "content_engagement": {
                    "articles": "High engagement",
                    "posts": "Medium engagement", 
                    "videos": "Growing engagement"
                },
                "professional_groups": [
                    f"{analysis_input.industry} Professionals",
                    "Industry Leaders Network",
                    "Business Innovation Group"
                ]
            }
        }

    async def _analyze_social_insights(
        self,
        analysis_input: PersonaAnalysisInput,
        keywords: Dict[str, List[str]],
        subreddits: List[str],
        social_research: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        AI-powered analysis of social media insights
        """
        try:
            chain = self.social_insights_prompt | self.llm | JsonOutputParser()
            
            result = await asyncio.to_thread(
                chain.invoke,
                {
                    "business_idea": analysis_input.business_idea,
                    "keywords": json.dumps(keywords, indent=2),
                    "communities": json.dumps(subreddits[:10], indent=2),
                    "target_market": analysis_input.target_market or "General market"
                }
            )
            
            return result if isinstance(result, dict) else self._fallback_insights(analysis_input)
            
        except Exception as e:
            print(f"Social insights analysis failed: {e}")
            return self._fallback_insights(analysis_input)

    def _fallback_keywords(self, analysis_input: PersonaAnalysisInput) -> Dict[str, List[str]]:
        """Fallback keywords when AI fails"""
        business_lower = analysis_input.business_idea.lower()
        
        # Extract some basic keywords from the business idea
        words = business_lower.split()
        primary = [word for word in words if len(word) > 3][:5]
        
        return {
            "primary_keywords": primary,
            "secondary_keywords": primary + ["software", "tool", "solution", "service", "platform"],
            "hashtags": [f"#{word}" for word in primary[:5]] + ["#business", "#productivity", "#innovation"],
            "problem_keywords": ["problem", "challenge", "issue", "difficulty", "frustration"],
            "solution_keywords": ["solution", "tool", "software", "service", "platform", "app"]
        }

    def _fallback_subreddits(self, analysis_input: PersonaAnalysisInput) -> List[str]:
        """Fallback subreddits when AI fails"""
        return [
            "entrepreneur", "smallbusiness", "startups", "business",
            "productivity", "software", "technology", "Innovation",
            "AskReddit", "YouShouldKnow", "LifeProTips", "personalfinance"
        ]

    def _fallback_insights(self, analysis_input: PersonaAnalysisInput) -> Dict[str, Any]:
        """Fallback insights when AI fails"""
        return {
            "demographics": {
                "age_ranges": ["25-35", "36-45", "46-55"],
                "gender_distribution": "Mixed",
                "locations": ["Urban areas", "Suburban areas"],
                "income_levels": ["$40k-$70k", "$70k-$100k", "$100k+"]
            },
            "behavioral_patterns": {
                "online_activity": ["Weekday evenings", "Weekend mornings"],
                "content_preferences": ["How-to content", "Reviews", "Case studies"],
                "engagement_style": ["Research-focused", "Comparison shopping"]
            },
            "pain_points": [
                "Time-consuming manual processes",
                "Lack of efficient solutions",
                "High costs of current alternatives",
                "Difficulty finding reliable options"
            ],
            "goals_motivations": [
                "Increase efficiency",
                "Save time and money",
                "Improve work quality",
                "Stay competitive"
            ],
            "communication_style": {
                "tone": "Professional but approachable",
                "terminology": ["efficient", "streamlined", "user-friendly"],
                "common_phrases": ["looking for", "any recommendations", "has anyone tried"]
            },
            "platform_preferences": {
                "primary": ["Google", "LinkedIn"],
                "secondary": ["Reddit", "YouTube", "Twitter"],
                "usage_context": "Research and professional networking"
            },
            "content_consumption": {
                "preferred_formats": ["Articles", "Videos", "Reviews"],
                "topics_of_interest": ["Industry trends", "Best practices", "Tool comparisons"],
                "engagement_triggers": ["Real examples", "Practical benefits", "Cost savings"]
            },
            "purchase_behavior": {
                "research_methods": ["Online search", "Peer recommendations", "Reviews"],
                "decision_factors": ["Price", "Features", "Ease of use", "Support"],
                "buying_journey": ["Problem recognition", "Research", "Evaluation", "Trial", "Purchase"]
            }
        }