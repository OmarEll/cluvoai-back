from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from contextlib import asynccontextmanager

from api.competitor_routes import router as competitor_router
from api.persona_routes import router as persona_router
from api.auth_routes import router as auth_router
from api.user_routes import router as user_router
from api.enhanced_analysis_routes import router as enhanced_analysis_router
from api.feedback_routes import router as feedback_router
from api.market_sizing_routes import router as market_sizing_router
from api.onboarding_routes import router as onboarding_router
from api.business_model_routes import router as business_model_router
from api.business_model_canvas_routes import router as business_model_canvas_router
from api.customer_discovery_routes import router as customer_discovery_router
from api.chat_routes import router as chat_router
from core.database import connect_to_mongo, close_mongo_connection, db
from config.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events
    """
    # Startup
    print("🚀 Cluvo.ai AI-Powered Business Intelligence API starting up...")
    
    # Validate required environment variables
    if not settings.openai_api_key:
        print("⚠️ WARNING: OPENAI_API_KEY environment variable is not set")
        print("🔄 Some AI features may not work properly")
    else:
        print("✅ OpenAI API key configured")
    
    # Connect to MongoDB
    try:
        await connect_to_mongo()
        print("✅ MongoDB connected successfully")
    except Exception as e:
        print(f"⚠️ MongoDB connection failed: {e}")
        print("🔄 Application will start without database connection. Some features may be limited.")
        print("💡 Make sure to set MONGO_USER, MONGO_PWD, and MONGO_HOST environment variables")
    
    print("✅ Environment variables validated")
    print(f"✅ Using LLM model: {settings.llm_model}")
    print("✅ Competitor Analysis API ready")
    print("✅ Persona Analysis API ready")
    print("✅ Market Sizing API ready")
    print("✅ Business Model API ready")
    print("✅ Business Model Canvas API ready")
    print("✅ Customer Discovery API ready")
    print("✅ Chat API ready")
    print("✅ Authentication API ready")
    print("✅ API ready to serve requests")
    
    yield
    
    # Shutdown
    print("🛑 Cluvo.ai API shutting down...")
    await close_mongo_connection()


# Create FastAPI app
app = FastAPI(
    title="Cluvo.ai - AI Business Intelligence API",
    description="AI-powered competitive intelligence and persona analysis for entrepreneurs",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(competitor_router, prefix="/api/v1", tags=["Competitor Analysis"])
app.include_router(persona_router, prefix="/api/v1", tags=["Persona Analysis"])
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(user_router, prefix="/api/v1/users", tags=["User Management"])
app.include_router(enhanced_analysis_router, prefix="/api/v1/enhanced", tags=["Enhanced Analysis"])
app.include_router(feedback_router, prefix="/api/v1", tags=["Feedback & Analytics"])
app.include_router(market_sizing_router, tags=["Market Sizing"])
app.include_router(onboarding_router, prefix="/api/v1", tags=["User Onboarding"])
app.include_router(business_model_router, prefix="/api/v1", tags=["Business Model Analysis"])
app.include_router(business_model_canvas_router, prefix="/api/v1", tags=["Business Model Canvas"])
app.include_router(customer_discovery_router, prefix="/api/v1", tags=["Customer Discovery"])
app.include_router(chat_router, prefix="/api/v1", tags=["Business Idea Chat"])


@app.get("/")
async def root():
    """
    Root endpoint and health check
    """
    return {
        "service": "Cluvo.ai AI Business Intelligence API",
        "version": "1.0.0",
        "status": "healthy",
        "database": "connected" if db.database is not None else "disconnected",
        "timestamp": "2024-01-01T00:00:00Z"
    }

@app.get("/health")
async def health_check():
    """
    Simple health check endpoint for Railway
    """
    return {"status": "ok"}


@app.get("/api/v1/features")
async def get_features():
    """
    List all available features
    """
    return {
        "status": "operational",
        "features": [
            "AI-powered competitor analysis",
            "Social media-driven persona analysis", 
            "Comprehensive market sizing with TAM/SAM/SOM",
            "Intelligent business model recommendations",
            "User authentication and registration",
            "Business idea management with intelligent onboarding",
            "Analysis history and storage",
            "User feedback and model performance tracking",
            "Cross-feature context integration for enhanced insights"
        ],
        "docs": "/docs"
    }


@app.get("/api/v1/features")
async def get_features():
    """
    List all available features
    """
    return {
        "competitor_analysis": {
            "description": "AI-powered competitive intelligence analysis",
            "endpoints": [
                "POST /api/v1/analyze/competitors",
                "POST /api/v1/analyze/competitors/async",
                "GET /api/v1/analyze/competitors/{analysis_id}"
            ],
            "capabilities": [
                "Automated competitor discovery",
                "Financial and pricing data collection",
                "SWOT analysis generation",
                "Market gap identification",
                "Strategic positioning recommendations",
                "Automatic result saving for authenticated users"
            ]
        },
        "persona_analysis": {
            "description": "Social media-driven target persona generation",
            "endpoints": [
                "POST /api/v1/analyze/personas",
                "POST /api/v1/analyze/personas/async", 
                "GET /api/v1/analyze/personas/{analysis_id}",
                "GET /api/v1/personas/example"
            ],
            "capabilities": [
                "AI-powered keyword and community discovery",
                "Social media platform analysis",
                "Detailed persona generation with pain points",
                "Market insights and targeting recommendations",
                "Content strategy recommendations",
                "Automatic result saving for authenticated users"
            ]
        },
        "authentication": {
            "description": "User registration and authentication system",
            "endpoints": [
                "POST /api/v1/auth/register",
                "POST /api/v1/auth/login",
                "GET /api/v1/auth/me",
                "GET /api/v1/auth/health"
            ],
            "capabilities": [
                "Secure user registration with validation",
                "JWT-based authentication", 
                "Password hashing with bcrypt",
                "User profile management",
                "MongoDB integration"
            ]
        },
        "user_management": {
            "description": "User profile and business idea management",
            "endpoints": [
                "GET /api/v1/users/profile",
                "PUT /api/v1/users/profile",
                "POST /api/v1/users/ideas",
                "GET /api/v1/users/ideas",
                "GET /api/v1/users/ideas/{idea_id}",
                "PUT /api/v1/users/ideas/{idea_id}",
                "DELETE /api/v1/users/ideas/{idea_id}",
                "GET /api/v1/users/ideas/{idea_id}/analyses",
                "GET /api/v1/users/analytics"
            ],
            "capabilities": [
                "Extended user profile with birthday and experience level",
                "Business idea CRUD operations",
                "Analysis result storage and history",
                "User analytics and insights",
                "Business stage and experience level management"
            ]
        },
        "feedback_system": {
            "description": "User feedback and model performance tracking",
            "endpoints": [
                "POST /api/v1/feedback",
                "PUT /api/v1/feedback/{analysis_id}",
                "GET /api/v1/feedback/{analysis_id}",
                "DELETE /api/v1/feedback/{analysis_id}",
                "GET /api/v1/feedback/analysis/{analysis_id}/summary",
                "GET /api/v1/feedback/my-history",
                "GET /api/v1/feedback/quick-rate/{analysis_id}",
                "GET /api/v1/analytics/performance/{analysis_type}"
            ],
            "capabilities": [
                "Like/dislike rating system",
                "Detailed comments and feedback",
                "Category-specific ratings",
                "1-5 score ratings for accuracy and usefulness",
                "Feedback history tracking",
                "Model performance analytics",
                "Quick rating for ease of use"
            ]
        }
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler
    """
    print(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error occurred"}
    )


if __name__ == "__main__":
    # Get port from environment variable (Railway sets PORT)
    port = int(os.environ.get("PORT", 8000))
    
    print(f"🚀 Starting Cluvo.ai API on port {port}")
    print(f"🌍 Environment: {os.environ.get('RAILWAY_ENVIRONMENT', 'development')}")
    print(f"🔗 Host: 0.0.0.0")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Disable reload in production
        log_level="info",
        access_log=True
    )