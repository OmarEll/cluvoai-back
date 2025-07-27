#!/usr/bin/env python3
"""
Test MongoDB connection for Cluvo.ai
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_connection():
    """Test MongoDB Atlas connection"""
    
    # Get credentials from environment
    mongo_user = os.getenv('MONGO_USER')
    mongo_pwd = os.getenv('MONGO_PWD')
    
    if not mongo_user or not mongo_pwd:
        print("❌ MongoDB credentials not found in .env file")
        print("Make sure MONGO_USER and MONGO_PWD are set")
        return False
    
    # Build connection string (exactly like in your example)
    connection_string = f"mongodb+srv://{mongo_user}:{mongo_pwd}@cluster0.cpe8ojr.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    
    try:
        print("🔌 Testing MongoDB Atlas connection...")
        print(f"👤 Username: {mongo_user}")
        print(f"🏠 Cluster: cluster0.cpe8ojr.mongodb.net")
        
        # Create client with ServerApi (as shown in your example)
        client = AsyncIOMotorClient(
            connection_string,
            server_api=ServerApi('1'),
            serverSelectionTimeoutMS=10000
        )
        
        # Test the connection
        await client.admin.command('ping')
        print("✅ Pinged your deployment. You successfully connected to MongoDB!")
        
        # List databases
        db_list = await client.list_database_names()
        print(f"📊 Available databases: {db_list}")
        
        # Test cluvoai database
        db = client.cluvoai
        collections = await db.list_collection_names()
        print(f"📁 Collections in 'cluvoai' database: {collections if collections else 'None (will be created on first write)'}")
        
        # Test creating a simple document
        test_collection = db.test_connection
        result = await test_collection.insert_one({"test": "connection", "status": "success"})
        print(f"✅ Test document inserted with ID: {result.inserted_id}")
        
        # Clean up test document
        await test_collection.delete_one({"_id": result.inserted_id})
        print("🧹 Test document cleaned up")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        print("\n💡 Troubleshooting:")
        print("1. Check your username and password")
        print("2. Make sure your IP address is whitelisted in MongoDB Atlas")
        print("3. Verify your cluster hostname")
        print("4. Check if your database user has proper permissions")
        return False

if __name__ == "__main__":
    print("🧪 Testing Cluvo.ai MongoDB Connection")
    print("=" * 40)
    
    success = asyncio.run(test_connection())
    
    if success:
        print("\n🎉 MongoDB connection test successful!")
        print("✅ Your application should now be able to connect to MongoDB")
    else:
        print("\n❌ MongoDB connection test failed")
        print("Please check the troubleshooting steps above") 