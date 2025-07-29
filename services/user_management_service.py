from datetime import datetime
from typing import List, Optional, Dict
import uuid
from fastapi import HTTPException, status
from pymongo.errors import DuplicateKeyError

import re
from core.user_models import (
    UserUpdate, UserResponse, BusinessIdea, BusinessIdeaCreate, BusinessIdeaUpdate,
    OnboardingQuestionnaire, BusinessLevel, MainGoal, BiggestChallenge, CurrentStage, GeographicFocus
)
from core.database import get_users_collection
from services.auth_service import auth_service


class UserManagementService:
    def __init__(self):
        self.users_collection = get_users_collection
    
    async def update_user_profile(self, user_email: str, user_update: UserUpdate) -> UserResponse:
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
        """Update a business idea"""
        try:
            # Build update document
            update_data = {"ideas.$.updated_at": datetime.utcnow()}
            
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
            # Add support for enhanced fields
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
        Process onboarding questionnaire and create an enhanced business idea
        """
        try:
            # Parse the business idea description to extract WHO, WHAT, HOW
            parsed_components = self._parse_business_idea_description(
                questionnaire.business_idea_description
            )
            
            # Generate a title from the description
            title = self._generate_business_idea_title(
                questionnaire.business_idea_description,
                parsed_components
            )
            
            # Create enhanced business idea
            business_idea_create = BusinessIdeaCreate(
                title=title,
                description=questionnaire.business_idea_description,
                current_stage=questionnaire.current_stage,
                main_goal=questionnaire.main_goal.value,
                biggest_challenge=questionnaire.biggest_challenge.value
            )
            
            # Create business idea in database
            created_idea = await self.create_business_idea(user_email, business_idea_create)
            
            # Enhance the created idea with onboarding-specific fields
            enhanced_idea_dict = created_idea.dict()
            enhanced_idea_dict.update({
                "business_level": questionnaire.business_level.value,
                "geographic_focus": questionnaire.geographic_focus.value,
                "target_who": parsed_components.get("who"),
                "problem_what": parsed_components.get("what"),
                "solution_how": parsed_components.get("how"),
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
        Generate personalized next steps and feature roadmap based on questionnaire responses
        """
        next_steps = []
        feature_roadmap = []
        
        # Recommendations based on current stage
        if questionnaire.current_stage == CurrentStage.IDEA:
            next_steps.extend([
                "Start with competitor analysis to understand your market landscape",
                "Research your target audience to validate your idea",
                "Define your unique value proposition"
            ])
            feature_roadmap.extend([
                {"feature": "competitor_analysis", "priority": "high", "reason": "Understand market competition"},
                {"feature": "persona_analysis", "priority": "high", "reason": "Identify target customers"},
                {"feature": "market_sizing", "priority": "medium", "reason": "Assess market opportunity"}
            ])
        
        elif questionnaire.current_stage == CurrentStage.VALIDATING:
            next_steps.extend([
                "Conduct persona analysis to better understand your customers",
                "Analyze market sizing to quantify your opportunity",
                "Study competitor strategies for positioning insights"
            ])
            feature_roadmap.extend([
                {"feature": "persona_analysis", "priority": "high", "reason": "Deep dive into customer needs"},
                {"feature": "market_sizing", "priority": "high", "reason": "Validate market size"},
                {"feature": "competitor_analysis", "priority": "medium", "reason": "Learn from competitors"}
            ])
        
        elif questionnaire.current_stage == CurrentStage.BUILDING:
            next_steps.extend([
                "Analyze market sizing to prioritize features",
                "Study competitor analysis for differentiation",
                "Use persona insights to guide product development"
            ])
            feature_roadmap.extend([
                {"feature": "market_sizing", "priority": "high", "reason": "Focus development efforts"},
                {"feature": "competitor_analysis", "priority": "medium", "reason": "Differentiate your product"},
                {"feature": "persona_analysis", "priority": "medium", "reason": "Build for right users"}
            ])
        
        elif questionnaire.current_stage == CurrentStage.LAUNCHING:
            next_steps.extend([
                "Finalize market sizing for go-to-market strategy",
                "Review competitor analysis for positioning",
                "Use persona insights for marketing messaging"
            ])
            feature_roadmap.extend([
                {"feature": "market_sizing", "priority": "high", "reason": "Size your go-to-market"},
                {"feature": "persona_analysis", "priority": "high", "reason": "Target right customers"},
                {"feature": "competitor_analysis", "priority": "medium", "reason": "Position against competition"}
            ])
        
        # Additional recommendations based on biggest challenge
        if questionnaire.biggest_challenge == BiggestChallenge.NEED_VALIDATION:
            next_steps.insert(0, "Run persona analysis to understand if people actually need your solution")
            
        elif questionnaire.biggest_challenge == BiggestChallenge.FIND_CUSTOMERS:
            next_steps.insert(0, "Use persona analysis to identify where your ideal customers spend time")
            
        elif questionnaire.biggest_challenge == BiggestChallenge.WHAT_TO_BUILD:
            next_steps.insert(0, "Start with competitor analysis to see what's already built and find gaps")
            
        elif questionnaire.biggest_challenge == BiggestChallenge.GET_SALES:
            next_steps.insert(0, "Analyze market sizing to understand pricing and sales potential")
            
        elif questionnaire.biggest_challenge == BiggestChallenge.OVERWHELMED:
            next_steps.insert(0, "Begin with one feature at a time - start with competitor analysis for market clarity")
        
        # Experience level adjustments
        if questionnaire.business_level == BusinessLevel.FIRST_TIME:
            next_steps.append("Take your time with each analysis - focus on learning from the insights")
        elif questionnaire.business_level == BusinessLevel.EXPERIENCED:
            next_steps.append("Leverage all three analyses together for comprehensive market intelligence")
        
        return next_steps[:5], feature_roadmap  # Limit to 5 next steps


# Create global instance
user_management_service = UserManagementService() 