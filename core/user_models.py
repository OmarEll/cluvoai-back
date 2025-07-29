from typing import Optional, List, Dict
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime, date
from enum import Enum


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


# Comprehensive Questionnaire Enums
class BusinessExperience(str, Enum):
    FIRST_TIME = "first_time_entrepreneur"
    STARTED_1_2 = "started_1_2_businesses"
    SERIAL_3_PLUS = "serial_entrepreneur_3_plus"
    CONSULTANT_ADVISOR = "business_consultant_advisor"


class BusinessStage(str, Enum):
    JUST_IDEA = "just_an_idea"
    VALIDATING = "validating_the_idea"
    BUILDING_MVP = "building_mvp"
    LAUNCHED_0_6_MONTHS = "launched_0_6_months"
    GROWING_6_PLUS_MONTHS = "growing_6_plus_months"
    SCALING_EXPANDING = "scaling_expanding"


class MainGoalNew(str, Enum):
    VALIDATE_IDEA = "validate_my_idea"
    UNDERSTAND_MARKET = "understand_the_market"
    FIND_CUSTOMERS = "find_customers"
    BUILD_PRODUCT = "build_the_product"
    GET_FUNDING = "get_funding"
    GROW_REVENUE = "grow_revenue"
    SCALE_OPERATIONS = "scale_operations"


class BiggestChallengeNew(str, Enum):
    IDEA_WONT_WORK = "dont_know_if_idea_will_work"
    UNDERSTANDING_COMPETITION = "understanding_competition"
    FINDING_CUSTOMERS = "finding_customers"
    BUILDING_PRODUCT = "building_the_product"
    GETTING_FUNDING = "getting_funding"
    MARKETING_SALES = "marketing_sales"
    TEAM_BUILDING = "team_building"
    OTHER = "other"


class GeographicFocusNew(str, Enum):
    LOCAL_CITY = "local_city"
    STATE_PROVINCE = "state_province"
    COUNTRY_WIDE = "country_wide"
    NORTH_AMERICA = "north_america"
    EUROPE = "europe"
    ASIA = "asia"
    GLOBAL = "global"
    OTHER = "other"


class TargetCustomerType(str, Enum):
    B2C_CONSUMERS = "individual_consumers_b2c"
    SMALL_BUSINESS_1_50 = "small_businesses_1_50_employees"
    MID_MARKET_51_500 = "mid_market_51_500_employees"
    ENTERPRISE_500_PLUS = "enterprise_500_plus_employees"
    GOVERNMENT_NONPROFIT = "government_nonprofit"
    OTHER = "other"


class TargetAgeGroup(str, Enum):
    AGE_18_25 = "18_25"
    AGE_26_35 = "26_35"
    AGE_36_45 = "36_45"
    AGE_46_55 = "46_55"
    AGE_55_PLUS = "55_plus"
    ALL_AGES = "all_ages"


class TargetIncome(str, Enum):
    UNDER_50K = "under_50k"
    FROM_50K_100K = "50k_100k"
    FROM_100K_250K = "100k_250k"
    OVER_250K = "250k_plus"
    ENTERPRISE_BUDGET = "enterprise_budget"
    NOT_RELEVANT = "not_relevant"


class Industry(str, Enum):
    TECHNOLOGY_SOFTWARE = "technology_software"
    HEALTHCARE = "healthcare"
    FINANCE_FINTECH = "finance_fintech"
    ECOMMERCE_RETAIL = "ecommerce_retail"
    EDUCATION = "education"
    REAL_ESTATE = "real_estate"
    MANUFACTURING = "manufacturing"
    FOOD_BEVERAGE = "food_beverage"
    PROFESSIONAL_SERVICES = "professional_services"
    ENTERTAINMENT_MEDIA = "entertainment_media"
    OTHER = "other"


class ProblemUrgency(str, Enum):
    CRITICAL = "critical_actively_seeking"
    IMPORTANT = "important_aware_not_urgent"
    NICE_TO_HAVE = "nice_to_have_not_actively_seeking"
    NOT_SURE = "not_sure"


class CompetitorKnowledge(str, Enum):
    KNOW_3_PLUS = "know_3_plus_direct_competitors"
    KNOW_1_2 = "know_1_2_competitors"
    SOME_IDEAS = "some_ideas_not_sure"
    DONT_KNOW = "dont_know_competitors"


class MonetizationModel(str, Enum):
    SUBSCRIPTION_SAAS = "subscription_saas"
    ONE_TIME_PURCHASE = "one_time_purchase"
    FREEMIUM = "freemium"
    MARKETPLACE_COMMISSION = "marketplace_commission"
    ADVERTISING = "advertising"
    CONSULTING_SERVICES = "consulting_services"
    NOT_SURE = "not_sure_yet"


class ExpectedPricing(str, Enum):
    FREE = "free"
    UNDER_10_MONTH = "under_10_month"
    FROM_10_50_MONTH = "10_50_month"
    FROM_50_200_MONTH = "50_200_month"
    OVER_200_MONTH = "200_plus_month"
    CUSTOM_PRICING = "custom_pricing"
    NOT_APPLICABLE = "not_applicable"


class AvailableBudget(str, Enum):
    UNDER_5K = "under_5k"
    FROM_5K_25K = "5k_25k"
    FROM_25K_100K = "25k_100k"
    FROM_100K_500K = "100k_500k"
    OVER_500K = "500k_plus"
    PRE_FUNDING = "pre_funding_seeking_investment"


class LaunchTimeline(str, Enum):
    WITHIN_3_MONTHS = "within_3_months"
    FROM_3_6_MONTHS = "3_6_months"
    FROM_6_12_MONTHS = "6_12_months"
    OVER_12_MONTHS = "12_plus_months"
    ALREADY_LAUNCHED = "already_launched"


class TimeCommitment(str, Enum):
    FULL_TIME_40_PLUS = "full_time_40_plus_hours"
    PART_TIME_20_39 = "part_time_20_39_hours"
    SIDE_PROJECT_5_19 = "side_project_5_19_hours"
    VERY_LIMITED_UNDER_5 = "very_limited_under_5_hours"


# Legacy enums for backward compatibility
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


class GeographicFocus(str, Enum):
    NORTH_AMERICA = "north_america"
    EUROPE = "europe"
    ASIA = "asia"
    AFRICA = "africa"
    SOUTH_AMERICA = "south_america"
    OCEANIA = "oceania"
    INTERNATIONAL = "international"


class BusinessIdea(BaseModel):
    id: Optional[str] = None
    title: str
    description: str
    current_stage: Optional[CurrentStage] = None
    main_goal: Optional[str] = None
    biggest_challenge: Optional[str] = None
    # Enhanced fields from onboarding
    business_level: Optional[BusinessLevel] = None
    geographic_focus: Optional[GeographicFocus] = None
    target_who: Optional[str] = None
    problem_what: Optional[str] = None
    solution_how: Optional[str] = None
    # Additional fields for analysis
    target_market: Optional[str] = None
    industry: Optional[str] = None
    # Feature completion tracking
    completed_analyses: List[str] = Field(default_factory=list)  # ["competitor", "persona", "market_sizing"]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_mongo(cls, data: dict):
        """Convert MongoDB document to BusinessIdea with legacy value handling"""
        if data is None:
            return None
        
        # Handle MongoDB _id field
        if "_id" in data and "id" not in data:
            data["id"] = str(data["_id"])
        
        # Handle legacy current_stage values
        if "current_stage" in data:
            stage_mapping = {
                "idea": "have_an_idea",
                "validating": "validating_idea", 
                "building": "building_product",
                "launching": "ready_to_launch"
            }
            if data["current_stage"] in stage_mapping:
                data["current_stage"] = stage_mapping[data["current_stage"]]
        
        return cls(**data)

    @classmethod
    def model_validate(cls, obj, *args, **kwargs):
        """Custom validation to handle legacy values"""
        if isinstance(obj, dict) and "current_stage" in obj:
            stage_mapping = {
                "idea": "have_an_idea",
                "validating": "validating_idea", 
                "building": "building_product",
                "launching": "ready_to_launch"
            }
            if obj["current_stage"] in stage_mapping:
                obj["current_stage"] = stage_mapping[obj["current_stage"]]
        
        return super().model_validate(obj, *args, **kwargs)

class BusinessIdeaCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)
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


class UserInDB(UserBase):
    id: Optional[str] = None
    hashed_password: Optional[str] = None
    role: UserRole = UserRole.USER
    email_verified: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Business ideas owned by this user
    ideas: List[BusinessIdea] = Field(default_factory=list)

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
        
        # Handle legacy current_stage values in the main data
        if "current_stage" in data:
            stage_mapping = {
                "idea": "have_an_idea",
                "validating": "validating_idea", 
                "building": "building_product",
                "launching": "ready_to_launch"
            }
            if data["current_stage"] in stage_mapping:
                data["current_stage"] = stage_mapping[data["current_stage"]]
        
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
    # Enhanced fields from onboarding
    business_level: Optional[BusinessLevel] = Field(None, description="Business experience level")
    geographic_focus: Optional[GeographicFocus] = Field(None, description="Target geographic focus")
    target_who: Optional[str] = Field(None, max_length=200, description="WHO we help")
    problem_what: Optional[str] = Field(None, max_length=500, description="WHAT problem we solve")
    solution_how: Optional[str] = Field(None, max_length=500, description="HOW we solve it")


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")


# New Comprehensive Onboarding Questionnaire
class OnboardingQuestionnaire(BaseModel):
    # Core Questions (Required)
    business_experience: BusinessExperience
    business_stage: BusinessStage
    business_idea: str = Field(..., min_length=10, max_length=500, description="Tell us about your business idea")
    main_goal: MainGoalNew
    biggest_challenge: BiggestChallengeNew
    geographic_focus: GeographicFocusNew

    # Target Audience Questions
    target_customer_type: TargetCustomerType
    target_age_group: List[TargetAgeGroup] = Field(..., description="What age group is your primary target? (Multiple select)")
    target_income: TargetIncome

    # Market Context
    industry: Industry
    problem_urgency: ProblemUrgency

    # Competitive Awareness
    competitor_knowledge: CompetitorKnowledge
    differentiation: Optional[str] = Field(None, max_length=500, description="What makes you different from existing solutions?")

    # Business Model
    monetization_model: MonetizationModel
    expected_pricing: ExpectedPricing

    # Resources & Timeline
    available_budget: AvailableBudget
    launch_timeline: LaunchTimeline
    time_commitment: TimeCommitment


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