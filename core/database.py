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
            connection_string = f"mongodb+srv://{settings.mongo_user}:{settings.mongo_pwd}@cluster0.cpe8ojr.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
        else:
            raise ValueError("MongoDB credentials are required. Please set MONGO_USER and MONGO_PWD in your .env file.")
        
        print("🔌 Connecting to MongoDB Atlas...")
        
        # Create the client with minimal configuration
        db.client = AsyncIOMotorClient(
            connection_string,
            server_api=ServerApi('1'),
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=5000
        )
        
        # Test the connection
        await db.client.admin.command('ping')
        
        # Set the database
        db.database = db.client[settings.mongo_database]
        
        print("✅ Connected to MongoDB Atlas successfully!")
        
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        raise


async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        db.client.close()
        print("🔌 Disconnected from MongoDB")


def get_database() -> AsyncIOMotorDatabase:
    """Get database instance"""
    return db.database


# Collection getters
def get_users_collection():
    """Get users collection"""
    if db.database is None:
        return None
    return db.database.users


def get_analyses_collection():
    """Get analyses collection for storing competitor analysis results"""
    if db.database is None:
        return None
    return db.database.analyses


def get_personas_collection():
    """Get personas collection for storing persona analysis results"""
    if db.database is None:
        return None
    return db.database.personas


def get_saved_analyses_collection():
    """Get saved analyses collection"""
    if db.database is None:
        return None
    return db.database.saved_analyses


def get_user_ideas_collection():
    """Get user ideas collection"""
    if db.database is None:
        return None
    return db.database.user_ideas


def get_feedback_collection():
    """Get feedback collection"""
    if db.database is None:
        return None
    return db.database.feedback 