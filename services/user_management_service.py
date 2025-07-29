from datetime import datetime
from typing import List, Optional, Dict
import uuid
from fastapi import HTTPException, status
from pymongo.errors import DuplicateKeyError

import re
from core.user_models import (
    BusinessIdea, BusinessIdeaCreate, BusinessIdeaUpdate,
    OnboardingQuestionnaire, BusinessLevel, MainGoal, BiggestChallenge, CurrentStage, GeographicFocus
)
from core.database import get_users_collection
from services.auth_service import auth_service


class UserManagementService:
    def __init__(self):
        self.users_collection = get_users_collection
    
    async def update_user_profile(self, user_email: str, user_update: Dict) -> Dict:
        """Update user profile information"""
        try:
            # Build update document
            update_data = {}
            if user_update.first_name is not None:
                update_data["first_name"] = user_update.first_name
            if user_update.last_name is not None:
                update_data["last_name"] = user_update.last_name
            if user_update.birthday is not None:
                update_data["birthday"] = user_update.birthday
            if user_update.experience_level is not None:
                update_data["experience_level"] = user_update.experience_level
            
            if not update_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No valid fields to update"
                )
            
            # Update user in database
            result = await self.users_collection().update_one(
                {"email": user_email.lower()},
                {"$set": update_data}
            )
            
            if result.matched_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Return updated user
            updated_user = await auth_service.get_user_by_email(user_email)
            if not updated_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found after update"
                )
            
            return UserResponse(
                id=updated_user.id,
                first_name=updated_user.first_name,
                last_name=updated_user.last_name,
                email=updated_user.email,
                birthday=getattr(updated_user, 'birthday', None),
                experience_level=getattr(updated_user, 'experience_level', None),
                role=updated_user.role,
                is_active=updated_user.is_active,
                created_at=updated_user.created_at,
                last_login=updated_user.last_login,
                ideas=await self.get_user_ideas(user_email)
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating user profile: {str(e)}"
            )
    
    async def create_business_idea(self, user_email: str, idea_data: BusinessIdeaCreate) -> BusinessIdea:
        """Create a new business idea for the user"""
        try:
            # Generate unique ID for the idea
            idea_id = str(uuid.uuid4())
            
            # Create the idea object
            new_idea = BusinessIdea(
                id=idea_id,
                title=idea_data.title,
                description=idea_data.description,
                current_stage=idea_data.current_stage,
                main_goal=idea_data.main_goal,
                biggest_challenge=idea_data.biggest_challenge,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Add idea to user's ideas array
            result = await self.users_collection().update_one(
                {"email": user_email.lower()},
                {"$push": {"ideas": new_idea.dict()}}
            )
            
            if result.matched_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            return new_idea
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating business idea: {str(e)}"
            )
    
    async def get_user_ideas(self, user_email: str) -> List[BusinessIdea]:
        """Get all business ideas for a user"""
        try:
            user_doc = await self.users_collection().find_one(
                {"email": user_email.lower()},
                {"ideas": 1}
            )
            
            if not user_doc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            ideas_data = user_doc.get("ideas", [])
            processed_ideas = []
            for idea in ideas_data:
                # Handle legacy current_stage values
                if "current_stage" in idea:
                    stage_mapping = {
                        "idea": "have_an_idea",
                        "validating": "validating_idea", 
                        "building": "building_product",
                        "launching": "ready_to_launch"
                    }
                    if idea["current_stage"] in stage_mapping:
                        idea["current_stage"] = stage_mapping[idea["current_stage"]]
                
                # Handle MongoDB _id field
                if "_id" in idea and "id" not in idea:
                    idea["id"] = str(idea["_id"])
                
                processed_ideas.append(BusinessIdea(**idea))
            
            return processed_ideas
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching user ideas: {str(e)}"
            )
    
    async def get_business_idea(self, user_email: str, idea_id: str) -> BusinessIdea:
        """Get a specific business idea by ID"""
        try:
            user_doc = await self.users_collection().find_one(
                {"email": user_email.lower(), "ideas.id": idea_id},
                {"ideas.$": 1}
            )
            
            if not user_doc or not user_doc.get("ideas"):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Business idea not found"
                )
            
            idea_data = user_doc["ideas"][0]
            
            # Handle legacy current_stage values
            if "current_stage" in idea_data:
                stage_mapping = {
                    "idea": "have_an_idea",
                    "validating": "validating_idea", 
                    "building": "building_product",
                    "launching": "ready_to_launch"
                }
                if idea_data["current_stage"] in stage_mapping:
                    idea_data["current_stage"] = stage_mapping[idea_data["current_stage"]]
            
            # Handle MongoDB _id field
            if "_id" in idea_data and "id" not in idea_data:
                idea_data["id"] = str(idea_data["_id"])
            
            return BusinessIdea(**idea_data)
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching business idea: {str(e)}"
            )
    
    async def get_business_idea_by_id(self, idea_id: str) -> Optional[BusinessIdea]:
        """Get a business idea by ID without user validation (for internal use)"""
        try:
            # Search across all users for the idea
            users = self.users_collection().find({"ideas.id": idea_id})
            
            async for user in users:
                if "ideas" in user:
                    for idea_data in user["ideas"]:
                        if idea_data.get("id") == idea_id:
                            # Handle legacy current_stage values
                            if "current_stage" in idea_data:
                                stage_mapping = {
                                    "idea": "have_an_idea",
                                    "validating": "validating_idea", 
                                    "building": "building_product",
                                    "launching": "ready_to_launch"
                                }
                                if idea_data["current_stage"] in stage_mapping:
                                    idea_data["current_stage"] = stage_mapping[idea_data["current_stage"]]
                            
                            # Handle MongoDB _id field
                            if "_id" in idea_data and "id" not in idea_data:
                                idea_data["id"] = str(idea_data["_id"])
                            
                            return BusinessIdea(**idea_data)
            
            return None
            
        except Exception as e:
            print(f"Error retrieving business idea by ID: {str(e)}")
            return None
    
    async def update_business_idea(self, user_email: str, idea_id: str, idea_update: BusinessIdeaUpdate) -> BusinessIdea:
        """Update a business idea with all comprehensive questionnaire fields"""
        try:
            # Build update document
            update_data = {"ideas.$.updated_at": datetime.utcnow()}
            
            # Core fields
            if idea_update.title is not None:
                update_data["ideas.$.title"] = idea_update.title
            if idea_update.description is not None:
                update_data["ideas.$.description"] = idea_update.description
            if idea_update.current_stage is not None:
                update_data["ideas.$.current_stage"] = idea_update.current_stage
            if idea_update.main_goal is not None:
                update_data["ideas.$.main_goal"] = idea_update.main_goal
            if idea_update.biggest_challenge is not None:
                update_data["ideas.$.biggest_challenge"] = idea_update.biggest_challenge
            if idea_update.target_market is not None:
                update_data["ideas.$.target_market"] = idea_update.target_market
            if idea_update.industry is not None:
                update_data["ideas.$.industry"] = idea_update.industry
            
            # Enhanced fields from onboarding (existing)
            if idea_update.business_level is not None:
                update_data["ideas.$.business_level"] = idea_update.business_level
            if idea_update.geographic_focus is not None:
                update_data["ideas.$.geographic_focus"] = idea_update.geographic_focus
            if idea_update.target_who is not None:
                update_data["ideas.$.target_who"] = idea_update.target_who
            if idea_update.problem_what is not None:
                update_data["ideas.$.problem_what"] = idea_update.problem_what
            if idea_update.solution_how is not None:
                update_data["ideas.$.solution_how"] = idea_update.solution_how
            
            # New comprehensive questionnaire fields (all 18 fields)
            # Core Questions
            if idea_update.business_experience is not None:
                update_data["ideas.$.business_experience"] = idea_update.business_experience
            if idea_update.business_stage is not None:
                update_data["ideas.$.business_stage"] = idea_update.business_stage
            if idea_update.main_goal_new is not None:
                update_data["ideas.$.main_goal_new"] = idea_update.main_goal_new
            if idea_update.biggest_challenge_new is not None:
                update_data["ideas.$.biggest_challenge_new"] = idea_update.biggest_challenge_new
            if idea_update.geographic_focus_new is not None:
                update_data["ideas.$.geographic_focus_new"] = idea_update.geographic_focus_new
            
            # Target Audience Questions
            if idea_update.target_customer_type is not None:
                update_data["ideas.$.target_customer_type"] = idea_update.target_customer_type
            if idea_update.target_age_group is not None:
                update_data["ideas.$.target_age_group"] = idea_update.target_age_group
            if idea_update.target_income is not None:
                update_data["ideas.$.target_income"] = idea_update.target_income
            
            # Market Context
            if idea_update.industry_new is not None:
                update_data["ideas.$.industry_new"] = idea_update.industry_new
            if idea_update.problem_urgency is not None:
                update_data["ideas.$.problem_urgency"] = idea_update.problem_urgency
            
            # Competitive Awareness
            if idea_update.competitor_knowledge is not None:
                update_data["ideas.$.competitor_knowledge"] = idea_update.competitor_knowledge
            if idea_update.differentiation is not None:
                update_data["ideas.$.differentiation"] = idea_update.differentiation
            
            # Business Model
            if idea_update.monetization_model is not None:
                update_data["ideas.$.monetization_model"] = idea_update.monetization_model
            if idea_update.expected_pricing is not None:
                update_data["ideas.$.expected_pricing"] = idea_update.expected_pricing
            
            # Resources & Timeline
            if idea_update.available_budget is not None:
                update_data["ideas.$.available_budget"] = idea_update.available_budget
            if idea_update.launch_timeline is not None:
                update_data["ideas.$.launch_timeline"] = idea_update.launch_timeline
            if idea_update.time_commitment is not None:
                update_data["ideas.$.time_commitment"] = idea_update.time_commitment
            
            # Update the idea
            result = await self.users_collection().update_one(
                {"email": user_email.lower(), "ideas.id": idea_id},
                {"$set": update_data}
            )
            
            if result.matched_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Business idea not found"
                )
            
            # Return the updated idea
            return await self.get_business_idea(user_email, idea_id)
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating business idea: {str(e)}"
            )
    
    async def delete_business_idea(self, user_email: str, idea_id: str) -> bool:
        """Delete a business idea"""
        try:
            result = await self.users_collection().update_one(
                {"email": user_email.lower()},
                {"$pull": {"ideas": {"id": idea_id}}}
            )
            
            if result.matched_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            if result.modified_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Business idea not found"
                )
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting business idea: {str(e)}"
            )

    async def process_onboarding_questionnaire(
        self, 
        user_email: str, 
        questionnaire: OnboardingQuestionnaire
    ) -> BusinessIdea:
        """
        Process comprehensive onboarding questionnaire and create an enhanced business idea
        """
        try:
            # Parse the business idea description to extract WHO, WHAT, HOW
            parsed_components = self._parse_business_idea_description(
                questionnaire.business_idea
            )
            
            # Generate a title from the description
            title = self._generate_business_idea_title(
                questionnaire.business_idea,
                parsed_components
            )
            
            # Map new enums to legacy enums for backward compatibility
            legacy_current_stage = self._map_business_stage_to_current_stage(questionnaire.business_stage)
            legacy_main_goal = self._map_main_goal_new_to_legacy(questionnaire.main_goal)
            legacy_biggest_challenge = self._map_biggest_challenge_new_to_legacy(questionnaire.biggest_challenge)
            legacy_business_level = self._map_business_experience_to_business_level(questionnaire.business_experience)
            legacy_geographic_focus = self._map_geographic_focus_new_to_legacy(questionnaire.geographic_focus)
            
            # Create enhanced business idea
            business_idea_create = BusinessIdeaCreate(
                title=title,
                description=questionnaire.business_idea,
                current_stage=legacy_current_stage,
                main_goal=legacy_main_goal,
                biggest_challenge=legacy_biggest_challenge
            )
            
            # Create business idea in database
            created_idea = await self.create_business_idea(user_email, business_idea_create)
            
            # Enhance the created idea with comprehensive onboarding fields
            enhanced_idea_dict = created_idea.dict()
            enhanced_idea_dict.update({
                "business_level": legacy_business_level.value if legacy_business_level else None,
                "geographic_focus": legacy_geographic_focus.value if legacy_geographic_focus else None,
                "target_who": parsed_components.get("who"),
                "problem_what": parsed_components.get("what"),
                "solution_how": parsed_components.get("how"),
                "target_market": self._derive_target_market_from_questionnaire(questionnaire),
                "industry": questionnaire.industry.value,
                "completed_analyses": []
            })
            
            return BusinessIdea(**enhanced_idea_dict)
            
        except Exception as e:
            print(f"Error processing onboarding questionnaire: {e}")
            raise Exception(f"Failed to process onboarding: {str(e)}")
    
    def _parse_business_idea_description(self, description: str) -> Dict[str, str]:
        """
        Parse business idea description to extract WHO, WHAT problem, HOW solution
        Expected format: "We help [WHO] solve [WHAT problem] by [HOW]"
        """
        components = {"who": None, "what": None, "how": None}
        
        try:
            # Try to match the exact format first
            pattern = r"we help (.+?) solve (.+?) by (.+?)(?:\.|$)"
            match = re.search(pattern, description.lower().strip())
            
            if match:
                components["who"] = match.group(1).strip()
                components["what"] = match.group(2).strip()
                components["how"] = match.group(3).strip()
            else:
                # Try alternative patterns
                # Pattern: "helping [WHO] with [WHAT] through [HOW]"
                alt_pattern1 = r"helping (.+?) with (.+?) through (.+?)(?:\.|$)"
                match1 = re.search(alt_pattern1, description.lower().strip())
                
                if match1:
                    components["who"] = match1.group(1).strip()
                    components["what"] = match1.group(2).strip()
                    components["how"] = match1.group(3).strip()
                else:
                    # Pattern: "for [WHO] to [WHAT/HOW]"
                    alt_pattern2 = r"for (.+?) to (.+?)(?:\.|$)"
                    match2 = re.search(alt_pattern2, description.lower().strip())
                    
                    if match2:
                        components["who"] = match2.group(1).strip()
                        components["how"] = match2.group(2).strip()
                        # Extract problem from context
                        components["what"] = self._extract_problem_from_context(description)
                    else:
                        # Fallback: use simple keyword extraction
                        components = self._extract_components_with_keywords(description)
            
        except Exception as e:
            print(f"Error parsing business idea description: {e}")
            # Return partial components if parsing fails
            pass
        
        return components
    
    def _extract_problem_from_context(self, description: str) -> str:
        """Extract problem statement from description context"""
        problem_keywords = [
            "problem", "issue", "challenge", "difficulty", "struggle", 
            "pain point", "frustration", "inefficiency", "lack of"
        ]
        
        sentences = description.split('.')
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(keyword in sentence_lower for keyword in problem_keywords):
                return sentence.strip()
        
        return "solve their challenges"
    
    def _extract_components_with_keywords(self, description: str) -> Dict[str, str]:
        """Extract components using keyword-based approach"""
        components = {"who": None, "what": None, "how": None}
        
        # Common target audience keywords
        who_keywords = [
            "businesses", "companies", "entrepreneurs", "startups", "users", 
            "customers", "people", "individuals", "teams", "organizations",
            "small business", "enterprises", "freelancers", "professionals"
        ]
        
        # Common solution keywords
        how_keywords = [
            "platform", "app", "software", "service", "tool", "system",
            "solution", "technology", "automation", "ai", "analytics"
        ]
        
        description_lower = description.lower()
        
        # Extract WHO
        for keyword in who_keywords:
            if keyword in description_lower:
                components["who"] = keyword
                break
        
        # Extract HOW
        for keyword in how_keywords:
            if keyword in description_lower:
                components["how"] = f"providing a {keyword}"
                break
        
        # Extract WHAT (fallback)
        if not components["what"]:
            components["what"] = "their key challenges"
        
        return components
    
    def _generate_business_idea_title(self, description: str, components: Dict[str, str]) -> str:
        """Generate a concise title for the business idea"""
        try:
            # If we have parsed components, create a structured title
            if components.get("who") and components.get("how"):
                who = components["who"].title()
                how = components["how"]
                
                # Clean up the "how" part for title
                if how.startswith("providing a "):
                    how = how.replace("providing a ", "").title()
                elif how.startswith("by "):
                    how = how.replace("by ", "").title()
                else:
                    how = how.title()
                
                return f"{how} for {who}"
            else:
                # Fallback: extract first meaningful part of description
                words = description.split()[:8]  # Take first 8 words
                title = " ".join(words)
                
                # Clean up the title
                title = title.replace("We help", "").replace("we help", "")
                title = title.replace("We are", "").replace("we are", "")
                title = title.strip()
                
                return title.title() if title else "New Business Idea"
                
        except Exception as e:
            print(f"Error generating title: {e}")
            return "New Business Idea"
    
    def generate_personalized_recommendations(
        self, 
        questionnaire: OnboardingQuestionnaire
    ) -> tuple[List[str], List[Dict[str, str]]]:
        """
        Generate personalized next steps and feature roadmap based on comprehensive questionnaire responses
        """
        next_steps = []
        feature_roadmap = []
        
        # Recommendations based on business stage (new comprehensive enum)
        if questionnaire.business_stage.value in ["just_an_idea"]:
            next_steps.extend([
                "Start with competitor analysis to understand your market landscape",
                "Research your target audience to validate your idea",
                "Define your unique value proposition",
                "Consider customer discovery to test core assumptions"
            ])
            feature_roadmap.extend([
                {"feature": "competitor_analysis", "priority": "high", "reason": "Understand market competition"},
                {"feature": "persona_analysis", "priority": "high", "reason": "Identify target customers"},
                {"feature": "customer_discovery", "priority": "medium", "reason": "Validate core assumptions"},
                {"feature": "market_sizing", "priority": "medium", "reason": "Assess market opportunity"}
            ])
        
        elif questionnaire.business_stage.value in ["validating_the_idea"]:
            next_steps.extend([
                "Conduct persona analysis to better understand your customers",
                "Run customer discovery interviews to validate assumptions",
                "Analyze market sizing to quantify your opportunity",
                "Study competitor strategies for positioning insights"
            ])
            feature_roadmap.extend([
                {"feature": "persona_analysis", "priority": "high", "reason": "Deep dive into customer needs"},
                {"feature": "customer_discovery", "priority": "high", "reason": "Validate with real customers"},
                {"feature": "market_sizing", "priority": "high", "reason": "Validate market size"},
                {"feature": "competitor_analysis", "priority": "medium", "reason": "Learn from competitors"}
            ])
        
        elif questionnaire.business_stage.value in ["building_mvp"]:
            next_steps.extend([
                "Analyze market sizing to prioritize features",
                "Study competitor analysis for differentiation opportunities",
                "Use persona insights to guide product development",
                "Plan business model around market insights"
            ])
            feature_roadmap.extend([
                {"feature": "market_sizing", "priority": "high", "reason": "Focus development efforts"},
                {"feature": "business_model", "priority": "high", "reason": "Define revenue strategy"},
                {"feature": "competitor_analysis", "priority": "medium", "reason": "Differentiate your product"},
                {"feature": "persona_analysis", "priority": "medium", "reason": "Build for right users"}
            ])
        
        elif questionnaire.business_stage.value in ["launched_0_6_months", "growing_6_plus_months"]:
            next_steps.extend([
                "Optimize market sizing for growth strategy",
                "Develop comprehensive business model canvas",
                "Analyze competitors for expansion opportunities",
                "Use persona insights for customer acquisition"
            ])
            feature_roadmap.extend([
                {"feature": "business_model_canvas", "priority": "high", "reason": "Optimize business model"},
                {"feature": "market_sizing", "priority": "high", "reason": "Plan growth strategy"},
                {"feature": "persona_analysis", "priority": "high", "reason": "Scale customer acquisition"},
                {"feature": "competitor_analysis", "priority": "medium", "reason": "Find growth opportunities"}
            ])
        
        elif questionnaire.business_stage.value in ["scaling_expanding"]:
            next_steps.extend([
                "Develop advanced business model strategies",
                "Analyze new market segments for expansion",
                "Study competitive landscape for strategic moves",
                "Optimize business model canvas for scale"
            ])
            feature_roadmap.extend([
                {"feature": "business_model_canvas", "priority": "high", "reason": "Optimize for scale"},
                {"feature": "market_sizing", "priority": "high", "reason": "Explore new markets"},
                {"feature": "business_model", "priority": "medium", "reason": "Advanced revenue strategies"},
                {"feature": "competitor_analysis", "priority": "medium", "reason": "Strategic positioning"}
            ])
        
        # Additional recommendations based on biggest challenge (new comprehensive enum)
        challenge_value = questionnaire.biggest_challenge.value
        
        if challenge_value in ["dont_know_if_idea_will_work"]:
            next_steps.insert(0, "Run persona analysis to understand if people actually need your solution")
            next_steps.insert(1, "Conduct customer discovery interviews to validate core assumptions")
            
        elif challenge_value in ["understanding_competition"]:
            next_steps.insert(0, "Start with comprehensive competitor analysis to map the competitive landscape")
            
        elif challenge_value in ["finding_customers"]:
            next_steps.insert(0, "Use persona analysis to identify where your ideal customers spend time")
            next_steps.insert(1, "Run customer discovery to understand customer acquisition channels")
            
        elif challenge_value in ["building_the_product"]:
            next_steps.insert(0, "Analyze competitors to see what's already built and identify gaps")
            next_steps.insert(1, "Use persona insights to prioritize features")
            
        elif challenge_value in ["getting_funding"]:
            next_steps.insert(0, "Develop comprehensive market sizing to show investment opportunity")
            next_steps.insert(1, "Create detailed business model canvas for investor presentations")
            
        elif challenge_value in ["marketing_sales"]:
            next_steps.insert(0, "Deep dive into persona analysis for marketing messaging")
            next_steps.insert(1, "Study competitor marketing strategies for positioning")
            
        elif challenge_value in ["team_building", "other"]:
            next_steps.insert(0, "Start with competitor analysis to understand market requirements")
        
        # Experience level adjustments (mapped from new business_experience enum)
        experience_value = questionnaire.business_experience.value
        
        if experience_value == "first_time_entrepreneur":
            next_steps.append("Take your time with each analysis - focus on learning from the insights")
            next_steps.append("Start with one analysis at a time to avoid feeling overwhelmed")
        elif experience_value in ["started_1_2_businesses", "serial_entrepreneur_3_plus"]:
            next_steps.append("Leverage your experience by comparing insights to previous ventures")
            next_steps.append("Consider advanced features like business model optimization")
        elif experience_value == "business_consultant_advisor":
            next_steps.append("Use comprehensive analyses to validate your advisory recommendations")
            next_steps.append("Consider all features to build complete market intelligence")
        
        # Main goal adjustments (new comprehensive enum)
        goal_value = questionnaire.main_goal.value
        
        if goal_value == "validate_my_idea":
            # Prioritize validation-focused features
            for item in feature_roadmap:
                if item["feature"] in ["persona_analysis", "customer_discovery"]:
                    item["priority"] = "high"
        elif goal_value == "understand_the_market":
            # Prioritize market intelligence features
            for item in feature_roadmap:
                if item["feature"] in ["market_sizing", "competitor_analysis"]:
                    item["priority"] = "high"
        elif goal_value in ["find_customers"]:
            # Prioritize customer-focused features
            for item in feature_roadmap:
                if item["feature"] in ["persona_analysis", "customer_discovery"]:
                    item["priority"] = "high"
        elif goal_value in ["get_funding", "grow_revenue", "scale_operations"]:
            # Prioritize business model features
            for item in feature_roadmap:
                if item["feature"] in ["business_model", "business_model_canvas", "market_sizing"]:
                    item["priority"] = "high"
        
        # Industry-specific recommendations
        industry_value = questionnaire.industry.value
        if industry_value == "technology_software":
            next_steps.append("Focus on competitive analysis - tech markets move quickly")
        elif industry_value in ["healthcare", "finance_fintech"]:
            next_steps.append("Pay special attention to regulatory considerations in your analysis")
        elif industry_value == "ecommerce_retail":
            next_steps.append("Analyze seasonal trends and customer behavior patterns")
        
        # Geographic focus adjustments
        geo_value = questionnaire.geographic_focus.value
        if geo_value in ["local_city", "state_province"]:
            next_steps.append("Focus on local market dynamics and regional competitors")
        elif geo_value == "global":
            next_steps.append("Consider cultural differences and regional market variations")
        
        # Customer type specific recommendations  
        customer_type = questionnaire.target_customer_type.value
        if customer_type == "individual_consumers_b2c":
            next_steps.append("Focus heavily on persona analysis for consumer behavior insights")
        elif customer_type in ["small_businesses_1_50_employees", "mid_market_51_500_employees", "enterprise_500_plus_employees"]:
            next_steps.append("Analyze B2B buying processes and decision-making hierarchies")
        
        # Budget and timeline reality check
        budget_value = questionnaire.available_budget.value
        timeline_value = questionnaire.launch_timeline.value
        
        if budget_value in ["under_5k", "5k_25k"] and timeline_value in ["within_3_months", "3_6_months"]:
            next_steps.append("Focus on essential analyses first given your timeline and budget constraints")
        elif budget_value in ["100k_500k", "500k_plus"]:
            next_steps.append("Consider comprehensive analysis across all features for strategic advantage")
        
        return next_steps[:8], feature_roadmap  # Limit to 8 next steps

    def _map_business_stage_to_current_stage(self, business_stage):
        """Map new BusinessStage to legacy CurrentStage"""
        from core.user_models import BusinessStage, CurrentStage
        
        mapping = {
            BusinessStage.JUST_IDEA: CurrentStage.IDEA,
            BusinessStage.VALIDATING: CurrentStage.VALIDATING,
            BusinessStage.BUILDING_MVP: CurrentStage.BUILDING,
            BusinessStage.LAUNCHED_0_6_MONTHS: CurrentStage.LAUNCHING,
            BusinessStage.GROWING_6_PLUS_MONTHS: CurrentStage.LAUNCHING,
            BusinessStage.SCALING_EXPANDING: CurrentStage.LAUNCHING
        }
        return mapping.get(business_stage, CurrentStage.IDEA)
    
    def _map_main_goal_new_to_legacy(self, main_goal):
        """Map new MainGoalNew to legacy MainGoal"""
        from core.user_models import MainGoalNew, MainGoal
        
        mapping = {
            MainGoalNew.VALIDATE_IDEA: MainGoal.VALIDATE_IDEA,
            MainGoalNew.UNDERSTAND_MARKET: MainGoal.VALIDATE_IDEA,
            MainGoalNew.FIND_CUSTOMERS: MainGoal.FIND_CUSTOMERS,
            MainGoalNew.BUILD_PRODUCT: MainGoal.BUILD_MVP,
            MainGoalNew.GET_FUNDING: MainGoal.GET_PAYING_CUSTOMERS,
            MainGoalNew.GROW_REVENUE: MainGoal.GET_PAYING_CUSTOMERS,
            MainGoalNew.SCALE_OPERATIONS: MainGoal.GET_PAYING_CUSTOMERS
        }
        return mapping.get(main_goal, MainGoal.VALIDATE_IDEA)
    
    def _map_biggest_challenge_new_to_legacy(self, biggest_challenge):
        """Map new BiggestChallengeNew to legacy BiggestChallenge"""
        from core.user_models import BiggestChallengeNew, BiggestChallenge
        
        mapping = {
            BiggestChallengeNew.IDEA_WONT_WORK: BiggestChallenge.NEED_VALIDATION,
            BiggestChallengeNew.UNDERSTANDING_COMPETITION: BiggestChallenge.NEED_VALIDATION,
            BiggestChallengeNew.FINDING_CUSTOMERS: BiggestChallenge.FIND_CUSTOMERS,
            BiggestChallengeNew.BUILDING_PRODUCT: BiggestChallenge.WHAT_TO_BUILD,
            BiggestChallengeNew.GETTING_FUNDING: BiggestChallenge.GET_SALES,
            BiggestChallengeNew.MARKETING_SALES: BiggestChallenge.GET_SALES,
            BiggestChallengeNew.TEAM_BUILDING: BiggestChallenge.OVERWHELMED,
            BiggestChallengeNew.OTHER: BiggestChallenge.OVERWHELMED
        }
        return mapping.get(biggest_challenge, BiggestChallenge.NEED_VALIDATION)
    
    def _map_business_experience_to_business_level(self, business_experience):
        """Map new BusinessExperience to legacy BusinessLevel"""
        from core.user_models import BusinessExperience, BusinessLevel
        
        mapping = {
            BusinessExperience.FIRST_TIME: BusinessLevel.FIRST_TIME,
            BusinessExperience.STARTED_1_2: BusinessLevel.SOME_EXPERIENCE,
            BusinessExperience.SERIAL_3_PLUS: BusinessLevel.EXPERIENCED,
            BusinessExperience.CONSULTANT_ADVISOR: BusinessLevel.EXPERIENCED
        }
        return mapping.get(business_experience, BusinessLevel.FIRST_TIME)
    
    def _map_geographic_focus_new_to_legacy(self, geographic_focus):
        """Map new GeographicFocusNew to legacy GeographicFocus"""
        from core.user_models import GeographicFocusNew, GeographicFocus
        
        mapping = {
            GeographicFocusNew.LOCAL_CITY: GeographicFocus.NORTH_AMERICA,  # Default to regional
            GeographicFocusNew.STATE_PROVINCE: GeographicFocus.NORTH_AMERICA,
            GeographicFocusNew.COUNTRY_WIDE: GeographicFocus.NORTH_AMERICA,
            GeographicFocusNew.NORTH_AMERICA: GeographicFocus.NORTH_AMERICA,
            GeographicFocusNew.EUROPE: GeographicFocus.EUROPE,
            GeographicFocusNew.ASIA: GeographicFocus.ASIA,
            GeographicFocusNew.GLOBAL: GeographicFocus.INTERNATIONAL,
            GeographicFocusNew.OTHER: GeographicFocus.INTERNATIONAL
        }
        return mapping.get(geographic_focus, GeographicFocus.INTERNATIONAL)
    
    def _derive_target_market_from_questionnaire(self, questionnaire) -> str:
        """Derive target market description from comprehensive questionnaire data"""
        components = []
        
        # Customer type
        if questionnaire.target_customer_type:
            customer_labels = {
                "individual_consumers_b2c": "individual consumers",
                "small_businesses_1_50_employees": "small businesses",
                "mid_market_51_500_employees": "mid-market companies",
                "enterprise_500_plus_employees": "enterprise organizations",
                "government_nonprofit": "government and non-profit organizations"
            }
            components.append(customer_labels.get(questionnaire.target_customer_type.value, "target customers"))
        
        # Age groups (if B2C)
        if (questionnaire.target_customer_type.value == "individual_consumers_b2c" and 
            questionnaire.target_age_group and 
            len(questionnaire.target_age_group) > 0):
            age_ranges = [age.value.replace("_", "-") for age in questionnaire.target_age_group]
            if len(age_ranges) <= 2:
                components.append(f"aged {' and '.join(age_ranges)}")
            else:
                components.append(f"across multiple age groups")
        
        # Income level
        if questionnaire.target_income and questionnaire.target_income.value != "not_relevant":
            income_labels = {
                "under_50k": "with lower income levels",
                "50k_100k": "with middle income levels", 
                "100k_250k": "with higher income levels",
                "250k_plus": "with high disposable income",
                "enterprise_budget": "with enterprise budgets"
            }
            if questionnaire.target_income.value in income_labels:
                components.append(income_labels[questionnaire.target_income.value])
        
        # Geographic focus
        if questionnaire.geographic_focus:
            geo_labels = {
                "local_city": "in local markets",
                "state_province": "at state/provincial level",
                "country_wide": "nationwide",
                "north_america": "in North America",
                "europe": "in Europe",
                "asia": "in Asia",
                "global": "globally",
                "other": "in targeted regions"
            }
            components.append(geo_labels.get(questionnaire.geographic_focus.value, ""))
        
        # Industry context
        if questionnaire.industry and questionnaire.industry.value != "other":
            industry_labels = {
                "technology_software": "in the technology sector",
                "healthcare": "in healthcare",
                "finance_fintech": "in finance and fintech",
                "ecommerce_retail": "in e-commerce and retail",
                "education": "in education",
                "real_estate": "in real estate",
                "manufacturing": "in manufacturing",
                "food_beverage": "in food and beverage",
                "professional_services": "in professional services",
                "entertainment_media": "in entertainment and media"
            }
            components.append(industry_labels.get(questionnaire.industry.value, ""))
        
        return " ".join(components).strip() or "target market"

    def generate_dynamic_roadmap(self, business_idea, completed_analyses) -> Dict:
        """
        Generate dynamic roadmap based on current stage and completed analyses
        """
        try:
            # Extract completed analysis types
            completed_types = []
            if completed_analyses:
                completed_types = [analysis.analysis_type for analysis in completed_analyses]
            
            next_steps = []
            priorities = []
            timeline = {}
            
            # Base recommendations on current stage
            current_stage = business_idea.current_stage if hasattr(business_idea, 'current_stage') else None
            
            if not completed_types:
                # No analyses completed yet
                next_steps = [
                    "Start with competitor analysis to understand your market",
                    "Follow with persona analysis to identify target customers", 
                    "Consider market sizing to quantify opportunity"
                ]
                priorities = [
                    {"feature": "competitor_analysis", "priority": "high", "reason": "Foundation market understanding"},
                    {"feature": "persona_analysis", "priority": "high", "reason": "Customer identification"},
                    {"feature": "market_sizing", "priority": "medium", "reason": "Market opportunity assessment"}
                ]
                timeline = {
                    "immediate": ["competitor_analysis"],
                    "short_term": ["persona_analysis"],
                    "medium_term": ["market_sizing"]
                }
            else:
                # Recommend next analyses based on what's completed
                remaining_features = []
                
                if "competitor" not in completed_types:
                    remaining_features.append({"feature": "competitor_analysis", "priority": "high"})
                    next_steps.append("Analyze competitors to understand market landscape")
                
                if "persona" not in completed_types:
                    remaining_features.append({"feature": "persona_analysis", "priority": "high"})
                    next_steps.append("Develop detailed customer personas")
                
                if "market_sizing" not in completed_types:
                    remaining_features.append({"feature": "market_sizing", "priority": "medium"})
                    next_steps.append("Size your market opportunity")
                
                if "business_model" not in completed_types:
                    remaining_features.append({"feature": "business_model", "priority": "medium"})
                    next_steps.append("Develop comprehensive business model")
                
                if "business_model_canvas" not in completed_types:
                    remaining_features.append({"feature": "business_model_canvas", "priority": "medium"})
                    next_steps.append("Create business model canvas")
                
                if "customer_discovery" not in completed_types:
                    remaining_features.append({"feature": "customer_discovery", "priority": "medium"})
                    next_steps.append("Conduct customer discovery interviews")
                
                priorities = remaining_features
                
                # Set timeline based on priority
                high_priority = [f["feature"] for f in remaining_features if f["priority"] == "high"]
                medium_priority = [f["feature"] for f in remaining_features if f["priority"] == "medium"]
                
                timeline = {
                    "immediate": high_priority[:2],
                    "short_term": high_priority[2:] + medium_priority[:2],
                    "medium_term": medium_priority[2:]
                }
                
                if not next_steps:
                    next_steps = [
                        "All core analyses complete!",
                        "Review insights for strategic planning",
                        "Consider developing go-to-market strategy"
                    ]
            
            return {
                "next_steps": next_steps[:5],
                "priorities": priorities[:6],
                "timeline": timeline
            }
            
        except Exception as e:
            print(f"Error generating dynamic roadmap: {e}")
            # Return default roadmap
            return {
                "next_steps": [
                    "Start with competitor analysis",
                    "Follow with persona analysis", 
                    "Consider market sizing analysis"
                ],
                "priorities": [
                    {"feature": "competitor_analysis", "priority": "high", "reason": "Market understanding"},
                    {"feature": "persona_analysis", "priority": "high", "reason": "Customer insights"},
                    {"feature": "market_sizing", "priority": "medium", "reason": "Market opportunity"}
                ],
                "timeline": {
                    "immediate": ["competitor_analysis"],
                    "short_term": ["persona_analysis"],
                    "medium_term": ["market_sizing"]
                }
            }


# Create global instance
user_management_service = UserManagementService() 