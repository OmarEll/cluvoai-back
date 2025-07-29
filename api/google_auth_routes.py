from fastapi import APIRouter, HTTPException, Request, status, Query
from fastapi.responses import RedirectResponse
import httpx
from urllib.parse import urlencode
import asyncio
from typing import Optional, Dict
import secrets
import uuid
from pydantic import BaseModel

from core.user_models import GoogleOAuthUser, Token, UserInDB
from services.google_oauth_service import google_oauth_service
from services.auth_service import auth_service
from config.settings import settings


router = APIRouter()


class GoogleAuthResponse(BaseModel):
    """Response model for successful Google authentication"""
    access_token: str
    token_type: str = "bearer"
    user: UserInDB
    message: str = "Successfully authenticated with Google"


class GoogleAuthUrl(BaseModel):
    """Response model for Google auth URL"""
    auth_url: str
    state: str
    message: str = "Navigate to auth_url to authenticate with Google"


@router.get("/google/auth-url", response_model=GoogleAuthUrl)
async def get_google_auth_url():
    """
    Get Google OAuth authorization URL
    """
    try:
        # Generate a random state for security
        state = str(uuid.uuid4())
        
        # Get Google authorization URL
        auth_url = google_oauth_service.get_authorization_url(state=state)
        
        return GoogleAuthUrl(
            auth_url=auth_url,
            state=state
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate Google auth URL: {str(e)}"
        )


@router.get("/google/callback")
async def google_oauth_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: Optional[str] = Query(None, description="State parameter for security"),
    error: Optional[str] = Query(None, description="Error from Google OAuth")
):
    """
    Handle Google OAuth callback
    """
    try:
        # Check for OAuth errors
        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Google OAuth error: {error}"
            )
        
        # Exchange authorization code for tokens and user info
        result = await google_oauth_service.exchange_code_for_token(code)
        
        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to exchange code for token: {result['error']}"
            )
        
        user_info = result['user_info']
        
        # Create GoogleOAuthUser from user info
        google_user = GoogleOAuthUser(
            google_id=user_info['id'],
            email=user_info['email'],
            first_name=user_info.get('given_name', ''),
            last_name=user_info.get('family_name', ''),
            profile_picture=user_info.get('picture'),
            verified_email=user_info.get('verified_email', True)
        )
        
        # Create or update user in database
        user_response = await auth_service.create_google_user(google_user)
        
        # Generate JWT token
        access_token = auth_service.create_access_token(
            data={"sub": user_response.email}
        )
        
        return GoogleAuthResponse(
            access_token=access_token,
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )


@router.post("/google/authenticate", response_model=GoogleAuthResponse)
async def authenticate_with_google_token(
    request: Request
):
    """
    Authenticate user with Google ID token (for frontend integration)
    """
    try:
        body = await request.json()
        id_token = body.get('id_token')
        
        if not id_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID token is required"
            )
        
        # Verify Google ID token
        user_info = google_oauth_service.verify_id_token(id_token)
        
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Google ID token"
            )
        
        # Create GoogleOAuthUser from token info
        google_user = GoogleOAuthUser(
            google_id=user_info['sub'],
            email=user_info['email'],
            first_name=user_info.get('given_name', ''),
            last_name=user_info.get('family_name', ''),
            profile_picture=user_info.get('picture'),
            verified_email=user_info.get('email_verified', True)
        )
        
        # Create or update user in database
        user_response = await auth_service.create_google_user(google_user)
        
        # Generate JWT token
        access_token = auth_service.create_access_token(
            data={"sub": user_response.email}
        )
        
        return GoogleAuthResponse(
            access_token=access_token,
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )


@router.get("/google/status")
async def google_oauth_status():
    """
    Check Google OAuth configuration status
    """
    return {
        "google_oauth_enabled": bool(settings.google_client_id and settings.google_client_secret),
        "google_client_id": settings.google_client_id[:10] + "..." if settings.google_client_id else None,
        "redirect_uri": settings.google_redirect_uri,
        "message": "Google OAuth configuration status"
    } 