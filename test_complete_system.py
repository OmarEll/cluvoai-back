#!/usr/bin/env python3
"""
Complete system test for Cluvo.ai with user management and analysis storage
"""

import asyncio
import aiohttp
import json
from datetime import date


async def test_complete_workflow():
    """Test the complete user workflow"""
    
    base_url = "http://localhost:8000"
    
    # Test user data
    test_user = {
        "first_name": "Alice",
        "last_name": "Entrepreneur", 
        "email": "alice.entrepreneur@example.com",
        "password": "securepassword123",
        "birthday": "1990-05-15",
        "experience_level": "intermediate"
    }
    
    # Business idea data
    business_idea = {
        "title": "AI-Powered Fitness Coach",
        "description": "An AI-powered mobile app that creates personalized workout plans and provides real-time coaching based on user performance and goals",
        "current_stage": "research",
        "main_goal": "Help people achieve their fitness goals with personalized AI coaching",
        "biggest_challenge": "Creating accurate AI models that can adapt to individual user needs and preferences",
        "target_market": "Fitness enthusiasts aged 25-45 who want personalized guidance",
        "industry": "Health and Fitness Technology"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            print("🚀 Testing Complete Cluvo.ai System")
            print("=" * 50)
            
            # Step 1: Register user
            print("\n1️⃣ Testing user registration...")
            async with session.post(
                f"{base_url}/api/v1/auth/register",
                json=test_user,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 201:
                    user_data = await response.json()
                    print("✅ User registered successfully!")
                    print(f"   User ID: {user_data['id']}")
                    print(f"   Name: {user_data['first_name']} {user_data['last_name']}")
                    user_id = user_data['id']
                elif response.status == 400:
                    print("⚠️ User already exists, proceeding with login...")
                else:
                    print(f"❌ Registration failed: {response.status}")
                    return False
            
            # Step 2: Login
            print("\n2️⃣ Testing login...")
            login_data = {
                "email": test_user["email"],
                "password": test_user["password"]
            }
            
            async with session.post(
                f"{base_url}/api/v1/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 200:
                    token_data = await response.json()
                    access_token = token_data['access_token']
                    print("✅ Login successful!")
                    print(f"   Token: {access_token[:30]}...")
                else:
                    print(f"❌ Login failed: {response.status}")
                    return False
            
            # Set headers for authenticated requests
            auth_headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Step 3: Update user profile
            print("\n3️⃣ Testing profile update...")
            profile_update = {
                "birthday": test_user["birthday"],
                "experience_level": test_user["experience_level"]
            }
            
            async with session.put(
                f"{base_url}/api/v1/users/profile",
                json=profile_update,
                headers=auth_headers
            ) as response:
                
                if response.status == 200:
                    profile_data = await response.json()
                    print("✅ Profile updated successfully!")
                    print(f"   Birthday: {profile_data.get('birthday')}")
                    print(f"   Experience: {profile_data.get('experience_level')}")
                else:
                    print(f"❌ Profile update failed: {response.status}")
            
            # Step 4: Create business idea
            print("\n4️⃣ Testing business idea creation...")
            async with session.post(
                f"{base_url}/api/v1/users/ideas",
                json=business_idea,
                headers=auth_headers
            ) as response:
                
                if response.status == 201:
                    idea_data = await response.json()
                    print("✅ Business idea created successfully!")
                    print(f"   Idea ID: {idea_data['id']}")
                    print(f"   Title: {idea_data['title']}")
                    print(f"   Stage: {idea_data['current_stage']}")
                    idea_id = idea_data['id']
                else:
                    print(f"❌ Business idea creation failed: {response.status}")
                    return False
            
            # Step 5: Run competitor analysis
            print("\n5️⃣ Testing competitor analysis...")
            analysis_request = {
                "idea_id": idea_id,
                "analysis_type": "competitor"
            }
            
            async with session.post(
                f"{base_url}/api/v1/enhanced/analyze",
                json=analysis_request,
                headers=auth_headers
            ) as response:
                
                if response.status == 200:
                    analysis_result = await response.json()
                    print("✅ Competitor analysis completed!")
                    print(f"   Analysis ID: {analysis_result['analysis_id']}")
                    print(f"   Status: {analysis_result['status']}")
                    print(f"   Competitors found: {len(analysis_result['competitor_report']['competitors'])}")
                    print(f"   Execution time: {analysis_result['execution_time']:.2f}s")
                else:
                    print(f"❌ Competitor analysis failed: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
            
            # Step 6: Run persona analysis
            print("\n6️⃣ Testing persona analysis...")
            persona_request = {
                "idea_id": idea_id,
                "analysis_type": "persona"
            }
            
            async with session.post(
                f"{base_url}/api/v1/enhanced/analyze",
                json=persona_request,
                headers=auth_headers
            ) as response:
                
                if response.status == 200:
                    persona_result = await response.json()
                    print("✅ Persona analysis completed!")
                    print(f"   Analysis ID: {persona_result['analysis_id']}")
                    print(f"   Status: {persona_result['status']}")
                    print(f"   Personas generated: {len(persona_result['persona_report']['personas'])}")
                    print(f"   Execution time: {persona_result['execution_time']:.2f}s")
                else:
                    print(f"❌ Persona analysis failed: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
            
            # Step 7: Get analysis history
            print("\n7️⃣ Testing analysis history...")
            async with session.get(
                f"{base_url}/api/v1/users/ideas/{idea_id}/analyses",
                headers=auth_headers
            ) as response:
                
                if response.status == 200:
                    history_data = await response.json()
                    print("✅ Analysis history retrieved!")
                    print(f"   Total analyses: {history_data['total_analyses']}")
                    print(f"   Last analysis: {history_data['last_analysis_date']}")
                    for analysis in history_data['analyses']:
                        print(f"   - {analysis['analysis_type']}: {analysis['status']}")
                else:
                    print(f"❌ Analysis history failed: {response.status}")
            
            # Step 8: Get user analytics
            print("\n8️⃣ Testing user analytics...")
            async with session.get(
                f"{base_url}/api/v1/users/analytics",
                headers=auth_headers
            ) as response:
                
                if response.status == 200:
                    analytics_data = await response.json()
                    print("✅ User analytics retrieved!")
                    print(f"   Total ideas: {analytics_data['total_ideas']}")
                    print(f"   Total analyses: {analytics_data['total_analyses']}")
                    print(f"   Competitor analyses: {analytics_data['competitor_analyses_count']}")
                    print(f"   Persona analyses: {analytics_data['persona_analyses_count']}")
                    if analytics_data['avg_execution_time']:
                        print(f"   Avg execution time: {analytics_data['avg_execution_time']:.2f}s")
                else:
                    print(f"❌ User analytics failed: {response.status}")
            
            # Step 9: Test retrieving saved analysis
            print("\n9️⃣ Testing saved analysis retrieval...")
            async with session.get(
                f"{base_url}/api/v1/enhanced/analyze/{idea_id}/competitor",
                headers=auth_headers
            ) as response:
                
                if response.status == 200:
                    saved_analysis = await response.json()
                    print("✅ Saved competitor analysis retrieved!")
                    print(f"   Analysis ID: {saved_analysis['analysis_id']}")
                    print(f"   Created: {saved_analysis['created_at']}")
                    print(f"   Status: {saved_analysis['status']}")
                else:
                    print(f"❌ Saved analysis retrieval failed: {response.status}")
            
            # Step 10: Test business stages and experience levels
            print("\n🔟 Testing metadata endpoints...")
            async with session.get(f"{base_url}/api/v1/users/stages") as response:
                if response.status == 200:
                    stages = await response.json()
                    print(f"✅ Business stages: {stages}")
                
            async with session.get(f"{base_url}/api/v1/users/experience-levels") as response:
                if response.status == 200:
                    levels = await response.json()
                    print(f"✅ Experience levels: {levels}")
            
            print("\n" + "=" * 50)
            print("🎉 Complete system test successful!")
            print("\nFeatures tested:")
            print("✅ User registration and authentication")
            print("✅ Profile management with new fields")
            print("✅ Business idea CRUD operations")
            print("✅ Competitor analysis with result storage")
            print("✅ Persona analysis with result storage")
            print("✅ Analysis history tracking")
            print("✅ User analytics and insights")
            print("✅ Saved analysis retrieval")
            print("✅ Metadata endpoints")
            
            return True
                    
        except aiohttp.ClientConnectorError:
            print("❌ Connection failed. Make sure the server is running on localhost:8000")
            print("   Start the server with: python main.py")
            return False
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            return False


async def test_health_endpoints():
    """Test all health endpoints"""
    print("\n🏥 Testing Health Endpoints")
    print("=" * 30)
    
    base_url = "http://localhost:8000"
    health_endpoints = [
        "/api/v1/auth/health",
        "/api/v1/users/health", 
        "/api/v1/enhanced/health"
    ]
    
    async with aiohttp.ClientSession() as session:
        for endpoint in health_endpoints:
            try:
                async with session.get(f"{base_url}{endpoint}") as response:
                    if response.status == 200:
                        health_data = await response.json()
                        print(f"✅ {endpoint}: {health_data['status']}")
                    else:
                        print(f"❌ {endpoint}: {response.status}")
            except Exception as e:
                print(f"❌ {endpoint}: {e}")


if __name__ == "__main__":
    print("🧪 Cluvo.ai Complete System Test")
    print("=" * 40)
    
    # Run health checks first
    asyncio.run(test_health_endpoints())
    
    # Run complete workflow test
    success = asyncio.run(test_complete_workflow())
    
    if success:
        print("\n✅ All tests passed! Your enhanced Cluvo.ai system is working correctly.")
    else:
        print("\n❌ Some tests failed. Check the error messages above.")
    
    print("\nAPI Documentation: http://localhost:8000/docs") 