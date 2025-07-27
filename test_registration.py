#!/usr/bin/env python3
"""
Simple test script for user registration API
"""

import asyncio
import aiohttp
import json


async def test_registration():
    """Test user registration endpoint"""
    
    # Test user data
    test_user = {
        "first_name": "John",
        "last_name": "Doe", 
        "email": "john.doe@example.com",
        "password": "securepassword123"
    }
    
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        try:
            # Test registration
            print("🧪 Testing user registration...")
            async with session.post(
                f"{base_url}/api/v1/auth/register",
                json=test_user,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 201:
                    user_data = await response.json()
                    print("✅ Registration successful!")
                    print(f"   User ID: {user_data['id']}")
                    print(f"   Name: {user_data['first_name']} {user_data['last_name']}")
                    print(f"   Email: {user_data['email']}")
                    print(f"   Created: {user_data['created_at']}")
                    
                    # Test login
                    print("\n🔑 Testing login...")
                    login_data = {
                        "email": test_user["email"],
                        "password": test_user["password"]
                    }
                    
                    async with session.post(
                        f"{base_url}/api/v1/auth/login",
                        json=login_data,
                        headers={"Content-Type": "application/json"}
                    ) as login_response:
                        
                        if login_response.status == 200:
                            token_data = await login_response.json()
                            print("✅ Login successful!")
                            print(f"   Token type: {token_data['token_type']}")
                            print(f"   Access token: {token_data['access_token'][:50]}...")
                            
                            # Test getting user info
                            print("\n👤 Testing user profile access...")
                            headers = {
                                "Authorization": f"Bearer {token_data['access_token']}",
                                "Content-Type": "application/json"
                            }
                            
                            async with session.get(
                                f"{base_url}/api/v1/auth/me",
                                headers=headers
                            ) as profile_response:
                                
                                if profile_response.status == 200:
                                    profile_data = await profile_response.json()
                                    print("✅ Profile access successful!")
                                    print(f"   Profile: {profile_data['first_name']} {profile_data['last_name']}")
                                    print(f"   Role: {profile_data['role']}")
                                    print(f"   Active: {profile_data['is_active']}")
                                else:
                                    print(f"❌ Profile access failed: {profile_response.status}")
                                    print(await profile_response.text())
                        else:
                            print(f"❌ Login failed: {login_response.status}")
                            print(await login_response.text())
                            
                elif response.status == 400:
                    error_data = await response.json()
                    if "Email already registered" in error_data.get("detail", ""):
                        print("⚠️ User already exists, testing login only...")
                        
                        # Test login with existing user
                        login_data = {
                            "email": test_user["email"],
                            "password": test_user["password"]
                        }
                        
                        async with session.post(
                            f"{base_url}/api/v1/auth/login",
                            json=login_data,
                            headers={"Content-Type": "application/json"}
                        ) as login_response:
                            
                            if login_response.status == 200:
                                token_data = await login_response.json()
                                print("✅ Login with existing user successful!")
                                print(f"   Access token: {token_data['access_token'][:50]}...")
                            else:
                                print(f"❌ Login failed: {login_response.status}")
                                print(await login_response.text())
                    else:
                        print(f"❌ Registration failed: {error_data}")
                else:
                    print(f"❌ Registration failed with status {response.status}")
                    print(await response.text())
                    
        except aiohttp.ClientConnectorError:
            print("❌ Connection failed. Make sure the server is running on localhost:8000")
            print("   Start the server with: python main.py")
        except Exception as e:
            print(f"❌ Test failed with error: {e}")


async def test_auth_health():
    """Test auth health endpoint"""
    print("\n🏥 Testing auth health endpoint...")
    
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{base_url}/api/v1/auth/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print("✅ Auth service is healthy!")
                    print(f"   Status: {health_data['status']}")
                    print(f"   Features: {', '.join(health_data['features'])}")
                else:
                    print(f"❌ Health check failed: {response.status}")
        except Exception as e:
            print(f"❌ Health check failed: {e}")


if __name__ == "__main__":
    print("🚀 Testing Cluvo.ai Authentication System")
    print("=" * 50)
    
    asyncio.run(test_auth_health())
    asyncio.run(test_registration())
    
    print("\n" + "=" * 50)
    print("🎉 Authentication tests completed!")
    print("\nTo start the server: python main.py")
    print("API Documentation: http://localhost:8000/docs") 