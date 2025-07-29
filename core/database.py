import asyncio
import os
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
        # Check for Railway MongoDB connection string first
        railway_mongo_url = os.environ.get("MONGODB_URL")
        
        if railway_mongo_url:
            # Use Railway's MongoDB connection string
            print("🔌 Connecting to Railway MongoDB...")
            connection_string = railway_mongo_url
        elif settings.mongo_user and settings.mongo_pwd:
            # Use the new MongoDB Atlas format with appName
            connection_string = f"mongodb+srv://{settings.mongo_user}:{settings.mongo_pwd}@{settings.mongo_host}/?retryWrites=true&w=majority&appName=Cluster0"
            print(f"🔌 Connecting to MongoDB at {settings.mongo_host}...")
        else:
            print("⚠️ No MongoDB credentials found - running without database")
            return
        
        # Create the client with minimal configuration
        db.client = AsyncIOMotorClient(
            connection_string,
            server_api=ServerApi('1'),
            serverSelectionTimeoutMS=5000,  # Shorter timeout for Railway
            connectTimeoutMS=5000,  # Shorter timeout for Railway
            socketTimeoutMS=5000  # Shorter timeout for Railway
        )
        
        # Test the connection with a short timeout
        await asyncio.wait_for(db.client.admin.command('ping'), timeout=5.0)
        
        # Set the database
        db.database = db.client[settings.mongo_database]
        
        print("✅ Connected to MongoDB successfully!")
        
    except asyncio.TimeoutError:
        print("⚠️ MongoDB connection timeout - continuing without database")
        print("💡 Database features will be limited")
    except Exception as e:
        print(f"⚠️ MongoDB connection failed: {str(e)[:100]}...")
        print("💡 Application will continue without database connection")
        # Don't raise the exception - let the app start without database


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