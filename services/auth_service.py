from datetime import datetime, timedelta
from typing import Optional
import bcrypt
from jose import JWTError, jwt
from pymongo.errors import DuplicateKeyError
from fastapi import HTTPException, status
import uuid

from core.user_models import UserCreate, UserInDB, UserRole, TokenData, GoogleOAuthUser
from core.database import get_users_collection
from config.settings import settings
from services.google_oauth_service import google_oauth_service


class AuthService:
    def __init__(self):
        self.users_collection = get_users_collection
    
    def _check_database_connection(self):
        """Check if database connection is available"""
        try:
            collection = self.users_collection()
            if collection is None:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Database connection is not available. Please try again later."
                )
            return collection
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Database connection error: {str(e)}"
            )
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password_bytes, salt)
        return hashed_password.decode('utf-8')
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> TokenData:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            email: str = payload.get("sub")
            if email is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            token_data = TokenData(email=email)
            return token_data
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    async def create_user(self, user_data: UserCreate) -> UserInDB:
        """Create a new user"""
        try:
            # Check database connection
            users_collection = self._check_database_connection()
            
            # Check if user already exists
            existing_user = await users_collection.find_one({"email": user_data.email})
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            
            # Hash password
            hashed_password = self.hash_password(user_data.password)
            
            # Create user document
            user_doc = {
                "id": str(uuid.uuid4()),
                "first_name": user_data.first_name,
                "last_name": user_data.last_name,
                "email": user_data.email,
                "hashed_password": hashed_password,
                "birthday": None,
                "experience_level": None,
                "google_id": None,
                "profile_picture": None,
                "is_oauth_user": user_data.is_oauth_user,
                "role": UserRole.USER,
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "ideas": []
            }
            
            # Insert user into database
            result = await users_collection.insert_one(user_doc)
            
            if result.inserted_id:
                return UserInDB.from_mongo(user_doc)
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create user"
                )
                
        except DuplicateKeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create user: {str(e)}"
            )
    
    async def create_google_user(self, google_user_data: GoogleOAuthUser) -> UserInDB:
        """Create a user from Google OAuth data"""
        try:
            # Check database connection
            users_collection = self._check_database_connection()
            
            # Check if user already exists by email or Google ID
            existing_user = await users_collection.find_one({
                "$or": [
                    {"email": google_user_data.email},
                    {"google_id": google_user_data.google_id}
                ]
            })
            
            if existing_user:
                # User exists, update their Google info if needed
                update_data = {
                    "google_id": google_user_data.google_id,
                    "profile_picture": google_user_data.profile_picture,
                    "is_oauth_user": True,
                    "updated_at": datetime.utcnow()
                }
                
                await users_collection.update_one(
                    {"id": existing_user["id"]},
                    {"$set": update_data}
                )
                
                return UserInDB.from_mongo(existing_user)
            
            # Create new user from Google data
            user_doc = {
                "id": str(uuid.uuid4()),
                "first_name": google_user_data.first_name,
                "last_name": google_user_data.last_name,
                "email": google_user_data.email,
                "hashed_password": None,  # No password for OAuth users
                "birthday": None,
                "experience_level": None,
                "google_id": google_user_data.google_id,
                "profile_picture": google_user_data.profile_picture,
                "is_oauth_user": True,
                "role": UserRole.USER,
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "ideas": []
            }
            
            # Insert user into database
            result = await users_collection.insert_one(user_doc)
            
            if result.inserted_id:
                return UserInDB.from_mongo(user_doc)
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create user"
                )
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create Google user: {str(e)}"
            )
    
    async def authenticate_user(self, email: str, password: str) -> Optional[UserInDB]:
        """Authenticate a user with email and password"""
        try:
            # Check database connection
            users_collection = self._check_database_connection()
            
            user_data = await users_collection.find_one({"email": email})
            if not user_data:
                return None
            
            # Check if this is an OAuth user (no password)
            if user_data.get("is_oauth_user", False) and not user_data.get("hashed_password"):
                return None
            
            if not self.verify_password(password, user_data["hashed_password"]):
                return None
            
            # Convert MongoDB document to UserInDB using the from_mongo method
            return UserInDB.from_mongo(user_data)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Authentication failed: {str(e)}"
            )
    
    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """Get user by email"""
        try:
            # Check database connection
            users_collection = self._check_database_connection()
            
            user_data = await users_collection.find_one({"email": email})
            if user_data:
                return UserInDB.from_mongo(user_data)
            return None
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get user: {str(e)}"
            )
    
    async def get_user_by_google_id(self, google_id: str) -> Optional[UserInDB]:
        """Get user by Google ID"""
        try:
            # Check database connection
            users_collection = self._check_database_connection()
            
            user_data = await users_collection.find_one({"google_id": google_id})
            if user_data:
                return UserInDB.from_mongo(user_data)
            return None
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get user: {str(e)}"
            )
    
    async def get_current_user_email(self, token: str) -> str:
        """Get current user email from token"""
        token_data = self.verify_token(token)
        return token_data.email

    async def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        """Get user by ID"""
        try:
            # Check database connection
            users_collection = self._check_database_connection()
            
            user_data = await users_collection.find_one({"id": user_id})
            if user_data:
                return UserInDB.from_mongo(user_data)
            return None
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get user: {str(e)}"
            )

    async def update_last_login(self, email: str):
        """Update user's last login timestamp"""
        try:
            # Check database connection
            users_collection = self._check_database_connection()
            
            await users_collection.update_one(
                {"email": email},
                {"$set": {"last_login": datetime.utcnow()}}
            )
        except HTTPException:
            raise
        except Exception as e:
            # Don't fail the login if this update fails
            print(f"Warning: Failed to update last login for {email}: {str(e)}")


# Create singleton instance
auth_service = AuthService() 