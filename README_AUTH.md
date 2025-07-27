# Cluvo.ai Authentication System

## 🔐 Overview

The Cluvo.ai backend now includes a complete user authentication system with MongoDB integration, JWT tokens, and secure password hashing.

## 🚀 Features

- **User Registration** with validation
- **JWT Authentication** with secure tokens
- **Password Hashing** using bcrypt
- **MongoDB Integration** for user storage
- **Email Validation** with proper format checking
- **User Profile Management**

## 📡 API Endpoints

### Authentication Routes (`/api/v1/auth/`)

#### 1. Register User
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com", 
  "password": "securepassword123"
}
```

**Response (201 Created):**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "role": "user",
  "is_active": true,
  "created_at": "2024-01-26T10:30:00.000Z",
  "last_login": null
}
```

#### 2. Login User
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "john.doe@example.com",
  "password": "securepassword123"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### 3. Get Current User
```http
GET /api/v1/auth/me
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "first_name": "John",
  "last_name": "Doe", 
  "email": "john.doe@example.com",
  "role": "user",
  "is_active": true,
  "created_at": "2024-01-26T10:30:00.000Z",
  "last_login": "2024-01-26T11:15:00.000Z"
}
```

#### 4. Health Check
```http
GET /api/v1/auth/health
```

## 🗄️ Database Schema

### Users Collection (`users`)

```javascript
{
  "_id": ObjectId("507f1f77bcf86cd799439011"),
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",  // Unique index
  "hashed_password": "$2b$12$...",
  "role": "user",  // "user" | "admin"
  "is_active": true,
  "created_at": ISODate("2024-01-26T10:30:00.000Z"),
  "last_login": ISODate("2024-01-26T11:15:00.000Z")
}
```

## ⚙️ Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# MongoDB Configuration
MONGO_USER=your_mongodb_username
MONGO_PWD=your_mongodb_password

# JWT Configuration (optional)
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Settings (`config/settings.py`)

```python
# MongoDB Configuration
mongo_user: str = ""
mongo_pwd: str = ""
mongo_host: str = "cluster0.wj29w.mongodb.net"
mongo_database: str = "cluvoai"

# JWT Configuration
jwt_secret_key: str = "your-super-secret-jwt-key-change-this-in-production"
jwt_algorithm: str = "HS256"
jwt_access_token_expire_minutes: int = 30
```

## 🧪 Testing

### Quick Test

1. **Start the server:**
   ```bash
   python main.py
   ```

2. **Run the test script:**
   ```bash
   python test_registration.py
   ```

### Manual Testing with curl

1. **Register a user:**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/auth/register" \
     -H "Content-Type: application/json" \
     -d '{
       "first_name": "John",
       "last_name": "Doe",
       "email": "john.doe@example.com",
       "password": "securepassword123"
     }'
   ```

2. **Login:**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "john.doe@example.com",
       "password": "securepassword123"
     }'
   ```

3. **Access protected route:**
   ```bash
   curl -X GET "http://localhost:8000/api/v1/auth/me" \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
   ```

## 🔒 Security Features

- **Password Hashing**: Uses bcrypt with salt for secure password storage
- **JWT Tokens**: Stateless authentication with configurable expiration
- **Email Validation**: Proper email format validation using `email-validator`
- **Unique Constraints**: Email uniqueness enforced at database level
- **Input Validation**: Pydantic models ensure data integrity
- **Error Handling**: Secure error messages without exposing sensitive data

## 🏗️ Architecture

### Core Components

1. **User Models** (`core/user_models.py`)
   - `UserCreate`: Registration input validation
   - `UserResponse`: Public user information
   - `UserInDB`: Internal user data with password hash
   - `Token`: JWT token response

2. **Database Connection** (`core/database.py`)
   - MongoDB connection management
   - Collection helpers
   - Index creation

3. **Authentication Service** (`services/auth_service.py`)
   - Password hashing and verification
   - JWT token creation and validation
   - User management operations

4. **API Routes** (`api/auth_routes.py`)
   - Registration endpoint
   - Login endpoint
   - User profile endpoint
   - Health check endpoint

## 🚀 Integration with Existing System

The authentication system integrates seamlessly with the existing Cluvo.ai competitor and persona analysis features:

- Users can register and login to access personalized analysis
- Analysis results can be tied to specific users
- Future features can leverage user authentication for premium functionality

## 🔮 Future Enhancements

- **Role-based access control** for admin features
- **Password reset functionality** via email
- **User analysis history** storage
- **API rate limiting** per user
- **Social login integration** (Google, GitHub)
- **Email verification** for new registrations

## 📝 Example Integration

```python
# Protecting competitor analysis routes
from api.auth_routes import security
from services.auth_service import auth_service

@router.post("/analyze/competitors")
async def analyze_competitors(
    request: CompetitorAnalysisRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # Verify user authentication
    token_data = auth_service.verify_token(credentials.credentials)
    user = await auth_service.get_user_by_email(token_data.email)
    
    # Run analysis...
    report = await workflow.run_analysis(business_input)
    
    # Save analysis to user's history
    await save_user_analysis(user.id, report)
    
    return report
```

This authentication system provides a solid foundation for user management and can be easily extended as the Cluvo.ai platform grows! 