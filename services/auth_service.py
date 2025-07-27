from datetime import datetime, timedelta
from typing import Optional
import bcrypt
from jose import JWTError, jwt
from pymongo.errors import DuplicateKeyError
from fastapi import HTTPException, status

from core.user_models import UserCreate, UserInDB, UserResponse, UserRole, TokenData
from core.database import get_users_collection
from config.settings import settings


class AuthService:
    def __init__(self):
        self.users_collection = get_users_collection
        
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
    
    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """Create a new user"""
        try:
            # Hash the password
            hashed_password = self.hash_password(user_data.password)
            
            # Prepare user document
            user_doc = {
                "first_name": user_data.first_name,
                "last_name": user_data.last_name,
                "email": user_data.email.lower(),  # Store email in lowercase
                "birthday": getattr(user_data, 'birthday', None),
                "experience_level": getattr(user_data, 'experience_level', None),
                "hashed_password": hashed_password,
                "role": UserRole.USER,
                "is_active": True,
                "created_at": datetime.utcnow(),
                "last_login": None,
                "ideas": []  # Initialize empty ideas array
            }
            
            # Insert user into database
            result = await self.users_collection().insert_one(user_doc)
            
            # Create response object
            user_response = UserResponse(
                id=str(result.inserted_id),
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                email=user_data.email,
                birthday=user_doc.get("birthday"),
                experience_level=user_doc.get("experience_level"),
                role=UserRole.USER,
                is_active=True,
                created_at=user_doc["created_at"],
                ideas=[]
            )
            
            return user_response
            
        except DuplicateKeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating user: {str(e)}"
            )
    
    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """Get user by email"""
        try:
            user_doc = await self.users_collection().find_one({"email": email.lower()})
            if user_doc:
                return UserInDB(
                    id=str(user_doc["_id"]),
                    first_name=user_doc["first_name"],
                    last_name=user_doc["last_name"],
                    email=user_doc["email"],
                    birthday=user_doc.get("birthday"),
                    experience_level=user_doc.get("experience_level"),
                    role=user_doc["role"],
                    is_active=user_doc["is_active"],
                    created_at=user_doc["created_at"],
                    last_login=user_doc.get("last_login"),
                    hashed_password=user_doc["hashed_password"],
                    ideas=[]  # Will be populated by user management service
                )
            return None
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching user: {str(e)}"
            )
    
    async def authenticate_user(self, email: str, password: str) -> Optional[UserInDB]:
        """Authenticate a user with email and password"""
        user = await self.get_user_by_email(email)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user
    
    async def update_last_login(self, email: str):
        """Update user's last login timestamp"""
        try:
            await self.users_collection().update_one(
                {"email": email.lower()},
                {"$set": {"last_login": datetime.utcnow()}}
            )
        except Exception as e:
            print(f"Error updating last login: {e}")
    
    async def get_current_user_email(self, token: str) -> str:
        """Get current user email from JWT token"""
        token_data = self.verify_token(token)
        return token_data.email


# Create global instance
auth_service = AuthService() 