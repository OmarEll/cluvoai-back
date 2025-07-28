import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API Keys
    openai_api_key: str = ""
    rapidapi_key: str = ""
    
    # Reddit API (optional)
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    
    # MongoDB Configuration
    mongo_user: str = ""
    mongo_pwd: str = ""
    mongo_host: str = "cluster0.wj29w.mongodb.net"
    mongo_database: str = "cluvoai"
    
    # JWT Configuration
    jwt_secret_key: str = "your-super-secret-jwt-key-change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    
    # Google OAuth Configuration
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/auth/oauth/google/callback"

    # LLM Configuration
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.3
    max_tokens: int = 2000
    
    # Scraping Configuration
    request_timeout: int = 15
    max_concurrent_requests: int = 5
    rate_limit_delay: float = 1.0
    
    # User Agent for web scraping
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    # Analysis Configuration
    max_competitors: int = 5
    min_competitors: int = 3
    
    # Data Sources Priority
    preferred_data_sources: List[str] = [
        "crunchbase",
        "linkedin", 
        "company_website",
        "social_media"
    ]
    
    # Cache Configuration
    enable_caching: bool = True
    cache_ttl: int = 3600  # 1 hour
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False
    
    class Config:
        env_file = ".env"
        extra = "allow"  # Allow extra fields from environment


settings = Settings() 