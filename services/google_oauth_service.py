import asyncio
import aiohttp
from typing import Optional, Dict, Any
from google.auth.transport.requests import Request
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from config.settings import settings
import json


class GoogleOAuthService:
    def __init__(self):
        self.client_id = settings.google_client_id
        self.client_secret = settings.google_client_secret
        self.redirect_uri = settings.google_redirect_uri
        
        # OAuth 2.0 scopes for user info
        self.scopes = [
            'openid',
            'email',
            'profile'
        ]
        
        # Google OAuth endpoints
        self.auth_url = "https://accounts.google.com/o/oauth2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        Generate Google OAuth authorization URL
        """
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(self.scopes),
            'response_type': 'code',
            'access_type': 'offline',
            'include_granted_scopes': 'true'
        }
        
        if state:
            params['state'] = state
        
        # Build URL with parameters
        param_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{self.auth_url}?{param_string}"
    
    async def exchange_code_for_token(self, authorization_code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token and user info
        """
        try:
            # Exchange code for tokens
            token_data = await self._get_access_token(authorization_code)
            
            # Get user information
            user_info = await self._get_user_info(token_data['access_token'])
            
            return {
                'success': True,
                'access_token': token_data['access_token'],
                'refresh_token': token_data.get('refresh_token'),
                'user_info': user_info
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _get_access_token(self, authorization_code: str) -> Dict[str, Any]:
        """
        Get access token from authorization code
        """
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': authorization_code,
            'grant_type': 'authorization_code',
            'redirect_uri': self.redirect_uri
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.token_url, data=data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Token exchange failed: {error_text}")
    
    async def _get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get user information from Google API
        """
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(self.userinfo_url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"User info retrieval failed: {error_text}")
    
    def verify_id_token(self, id_token_string: str) -> Optional[Dict[str, Any]]:
        """
        Verify Google ID token and extract user info
        """
        try:
            # Verify the token
            idinfo = id_token.verify_oauth2_token(
                id_token_string, 
                Request(), 
                self.client_id
            )
            
            # Verify the issuer
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')
            
            return idinfo
            
        except ValueError as e:
            print(f"ID token verification failed: {e}")
            return None
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh token
        """
        try:
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.token_url, data=data) as response:
                    if response.status == 200:
                        token_data = await response.json()
                        return {
                            'success': True,
                            'access_token': token_data['access_token'],
                            'expires_in': token_data.get('expires_in')
                        }
                    else:
                        error_text = await response.text()
                        return {
                            'success': False,
                            'error': f"Token refresh failed: {error_text}"
                        }
                        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


# Create singleton instance
google_oauth_service = GoogleOAuthService() 