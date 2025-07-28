from typing import Optional, List, Dict
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime, date
from enum import Enum


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


class ExperienceLevel(str, Enum):
    FIRST_TIME = "first_time_entrepreneur"
    SOME_EXPERIENCE = "some_experience"
    EXPERIENCED = "experienced_entrepreneur"


class CurrentStage(str, Enum):
    IDEA = "have_an_idea"
    VALIDATING = "validating_idea"
    BUILDING = "building_product"
    LAUNCHING = "ready_to_launch"


class BusinessLevel(str, Enum):
    FIRST_TIME = "first_time_entrepreneur"
    SOME_EXPERIENCE = "some_experience"  # 5-10 years
    EXPERIENCED = "experienced_entrepreneur"


class MainGoal(str, Enum):
    VALIDATE_IDEA = "validate_if_people_want_idea"
    FIND_CUSTOMERS = "find_and_talk_to_customers"
    BUILD_MVP = "build_first_version_mvp"
    GET_PAYING_CUSTOMERS = "get_first_paying_customers"


class BiggestChallenge(str, Enum):
    NEED_VALIDATION = "dont_know_if_anyone_needs_this"
    FIND_CUSTOMERS = "dont_know_how_to_find_customers"
    WHAT_TO_BUILD = "dont_know_what_to_build_first"
    GET_SALES = "dont_know_how_to_get_people_to_buy"
    OVERWHELMED = "feel_overwhelmed_dont_know_where_to_start"


class BusinessIdea(BaseModel):
    id: Optional[str] = None
    title: str
    description: str
    current_stage: Optional[CurrentStage] = None
    main_goal: Optional[str] = None
    biggest_challenge: Optional[str] = None
    # Enhanced fields from onboarding
    business_level: Optional[BusinessLevel] = None
    target_who: Optional[str] = None
    problem_what: Optional[str] = None
    solution_how: Optional[str] = None
    # Feature completion tracking
    completed_analyses: List[str] = Field(default_factory=list)  # ["competitor", "persona", "market_sizing"]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class BusinessIdeaCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)
    current_stage: Optional[CurrentStage] = None
    main_goal: Optional[str] = None
    biggest_challenge: Optional[str] = None

class BusinessIdeaUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=2000)
    current_stage: Optional[CurrentStage] = None
    main_goal: Optional[str] = None
    biggest_challenge: Optional[str] = None


class UserBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50, description="User's first name")
    last_name: str = Field(..., min_length=1, max_length=50, description="User's last name")
    email: EmailStr = Field(..., description="User's email address")
    birthday: Optional[date] = Field(None, description="User's birth date")
    experience_level: Optional[ExperienceLevel] = Field(None, description="User's business experience level")
    
    # Google OAuth fields
    google_id: Optional[str] = Field(None, description="User's Google ID")
    profile_picture: Optional[str] = Field(None, description="User's profile picture URL")
    is_oauth_user: bool = Field(default=False, description="Whether user signed up via OAuth")


class UserCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50, description="User's first name")
    last_name: str = Field(..., min_length=1, max_length=50, description="User's last name")
    email: EmailStr = Field(..., description="User's email address")
    is_oauth_user: bool = Field(default=False, description="Whether user signed up via OAuth")
    password: str = Field(..., min_length=8, max_length=128, description="User's password")


class GoogleOAuthUser(BaseModel):
    """Model for Google OAuth user data"""
    google_id: str = Field(..., description="User's Google ID")
    email: EmailStr = Field(..., description="User's email address")
    first_name: str = Field(..., description="User's first name")
    last_name: str = Field(..., description="User's last name")
    profile_picture: Optional[str] = Field(None, description="User's profile picture URL")
    verified_email: bool = Field(default=True, description="Whether email is verified by Google")


class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=50, description="User's first name")
    last_name: Optional[str] = Field(None, min_length=1, max_length=50, description="User's last name")
    birthday: Optional[date] = Field(None, description="User's birth date")
    experience_level: Optional[ExperienceLevel] = Field(None, description="User's business experience level")


class UserResponse(UserBase):
    id: str = Field(..., description="User's unique identifier")
    role: UserRole = Field(default=UserRole.USER, description="User's role")
    is_active: bool = Field(default=True, description="Whether the user is active")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="User creation timestamp")
    last_login: Optional[datetime] = Field(None, description="User's last login timestamp")
    ideas: List[BusinessIdea] = Field(default_factory=list, description="User's business ideas")


class UserInDB(UserResponse):
    hashed_password: str = Field(..., description="User's hashed password")
    
    class Config:
        # Allow extra fields from MongoDB
        extra = "allow"
        
    @classmethod
    def from_mongo(cls, data: dict):
        """Convert MongoDB document to UserInDB"""
        if data is None:
            return None
        
        # Handle MongoDB _id field
        if "_id" in data and "id" not in data:
            data["id"] = str(data["_id"])
        
        # Handle legacy current_stage values
        if "ideas" in data and isinstance(data["ideas"], list):
            for idea in data["ideas"]:
                if isinstance(idea, dict) and "current_stage" in idea:
                    # Map legacy values to new enum values
                    stage_mapping = {
                        "idea": "have_an_idea",
                        "validating": "validating_idea", 
                        "building": "building_product",
                        "launching": "ready_to_launch"
                    }
                    if idea["current_stage"] in stage_mapping:
                        idea["current_stage"] = stage_mapping[idea["current_stage"]]
        
        return cls(**data)


class BusinessIdeaCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100, description="Brief title for the idea")
    description: str = Field(..., min_length=10, max_length=1000, description="Detailed description of the business idea")
    current_stage: CurrentStage = Field(..., description="Current development stage")
    main_goal: str = Field(..., min_length=5, max_length=500, description="Primary goal for this idea")
    biggest_challenge: str = Field(..., min_length=5, max_length=500, description="Biggest challenge faced")
    target_market: Optional[str] = Field(None, max_length=200, description="Target market description")
    industry: Optional[str] = Field(None, max_length=100, description="Industry vertical")


class BusinessIdeaUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100, description="Brief title for the idea")
    description: Optional[str] = Field(None, min_length=10, max_length=1000, description="Detailed description of the business idea")
    current_stage: Optional[CurrentStage] = Field(None, description="Current development stage")
    main_goal: Optional[str] = Field(None, min_length=5, max_length=500, description="Primary goal for this idea")
    biggest_challenge: Optional[str] = Field(None, min_length=5, max_length=500, description="Biggest challenge faced")
    target_market: Optional[str] = Field(None, max_length=200, description="Target market description")
    industry: Optional[str] = Field(None, max_length=100, description="Industry vertical")


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")


# Enums have been moved to the top of the file

class OnboardingQuestionnaire(BaseModel):
    business_level: BusinessLevel
    current_stage: CurrentStage
    business_idea_description: str = Field(..., description="Business idea in format: We help [WHO] solve [WHAT problem] by [HOW]")
    main_goal: MainGoal
    biggest_challenge: BiggestChallenge

class EnhancedBusinessIdea(BaseModel):
    title: str
    description: str
    # Onboarding questionnaire data
    business_level: Optional[BusinessLevel] = None
    current_stage: Optional[CurrentStage] = None
    main_goal: Optional[MainGoal] = None
    biggest_challenge: Optional[BiggestChallenge] = None
    # Structured business idea components
    target_who: Optional[str] = None  # WHO we help
    problem_what: Optional[str] = None  # WHAT problem we solve
    solution_how: Optional[str] = None  # HOW we solve it
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class OnboardingRequest(BaseModel):
    questionnaire: OnboardingQuestionnaire

class OnboardingResponse(BaseModel):
    message: str
    business_idea: BusinessIdea
    recommended_next_steps: List[str]
    feature_roadmap: List[Dict[str, str]] 