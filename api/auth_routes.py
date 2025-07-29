from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import timedelta
from typing import Optional

from core.user_models import UserCreate, UserLogin, Token, UserInDB
from services.auth_service import auth_service
from services.google_oauth_service import google_oauth_service
from config.settings import settings
from api.google_auth_routes import router as google_auth_router

router = APIRouter()
security = HTTPBearer()

# Include Google OAuth routes
router.include_router(google_auth_router, prefix="/oauth", tags=["Google OAuth"])


@router.post("/register", response_model=UserInDB, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate):
    """
    Register a new user
    """
    try:
        # Create the user
        user = await auth_service.create_user(user_data)
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=Token)
async def login_user(user_credentials: UserLogin):
    """
    Login a user and return access token
    """
    try:
        # Authenticate user
        user = await auth_service.authenticate_user(
            user_credentials.email, 
            user_credentials.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
        access_token = auth_service.create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        
        # Update last login
        await auth_service.update_last_login(user.email)
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.get("/me", response_model=UserInDB)
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get current user information
    """
    try:
        # Verify token
        token_data = auth_service.verify_token(credentials.credentials)
        
        # Get user from database
        user = await auth_service.get_user_by_email(token_data.email)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user: {str(e)}"
        )


@router.get("/health")
async def auth_health_check():
    """
    Health check for auth service
    """
    return {
        "status": "healthy",
        "service": "authentication",
        "features": [
            "User registration",
            "User login", 
            "JWT token authentication",
            "User profile access"
        ]
    } 