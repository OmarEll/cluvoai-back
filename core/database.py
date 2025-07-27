import asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ServerSelectionTimeoutError
from pymongo.server_api import ServerApi
from config.settings import settings


class MongoDB:
    client: AsyncIOMotorClient = None
    database: AsyncIOMotorDatabase = None


db = MongoDB()


async def connect_to_mongo():
    """Create database connection"""
    try:
        # Build MongoDB connection string for Atlas
        if settings.mongo_user and settings.mongo_pwd:
            # Your MongoDB Atlas connection (updated with correct cluster)
            connection_string = f"mongodb+srv://{settings.mongo_user}:{settings.mongo_pwd}@cluster0.cpe8ojr.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
        else:
            raise ValueError("MongoDB credentials are required. Please set MONGO_USER and MONGO_PWD in your .env file.")
        
        print("🔌 Connecting to MongoDB Atlas...")
        
        # Create the client with ServerApi and SSL configuration for Railway
        db.client = AsyncIOMotorClient(
            connection_string, 
            server_api=ServerApi('1'),
            serverSelectionTimeoutMS=20000,
            connectTimeoutMS=20000,
            socketTimeoutMS=20000,
            tls=True,
            tlsAllowInvalidCertificates=False,
            tlsAllowInvalidHostnames=False,
            retryWrites=True,
            w='majority'
        )
        
        # Test the connection
        await db.client.admin.command('ping')
        
        # Set the database
        db.database = db.client[settings.mongo_database]
        
        # Create indexes for users collection
        await create_indexes()
        
        print("✅ Connected to MongoDB Atlas successfully!")
        
    except ServerSelectionTimeoutError as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        raise
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        raise


async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        db.client.close()
        print("🔌 Disconnected from MongoDB")


async def create_indexes():
    """Create database indexes for better performance"""
    try:
        # Create unique index on email for users collection
        await db.database.users.create_index("email", unique=True)
        
        # Create indexes for saved analyses
        await db.database.saved_analyses.create_index([("user_id", 1), ("idea_id", 1)])
        await db.database.saved_analyses.create_index([("user_id", 1), ("analysis_type", 1)])
        await db.database.saved_analyses.create_index([("created_at", -1)])
        
        # Create indexes for user ideas (if we need to query them separately)
        await db.database.users.create_index("ideas.id")
        
        # Create indexes for feedback
        await db.database.feedback.create_index([("analysis_id", 1)])
        await db.database.feedback.create_index([("user_id", 1)])
        await db.database.feedback.create_index([("analysis_type", 1), ("rating", 1)])
        await db.database.feedback.create_index([("created_at", -1)])
        await db.database.feedback.create_index([("user_id", 1), ("analysis_id", 1)], unique=True)
        
        print("✅ Database indexes created successfully!")
    except Exception as e:
        print(f"⚠️ Error creating indexes: {e}")


def get_database() -> AsyncIOMotorDatabase:
    """Get database instance"""
    return db.database


# Collection getters
def get_users_collection():
    """Get users collection"""
    return db.database.users


def get_analyses_collection():
    """Get analyses collection for storing competitor analysis results"""
    return db.database.analyses


def get_personas_collection():
    """Get personas collection for storing persona analysis results"""
    return db.database.personas


def get_saved_analyses_collection():
    """Get saved analyses collection for storing user analysis results"""
    return db.database.saved_analyses


def get_user_ideas_collection():
    """Get user ideas collection (embedded in users, but can be used for indexing)"""
    return db.database.user_ideas


def get_feedback_collection():
    """Get feedback collection for storing user feedback on analysis results"""
    return db.database.feedback 