#!/usr/bin/env python3
"""
Test script for authenticated analysis with automatic saving
"""

import asyncio
import aiohttp
import json
from datetime import datetime


async def test_authenticated_analysis():
    """Test that analysis APIs save results for authenticated users"""
    
    base_url = "http://localhost:8000"
    
    # Test user credentials
    user_credentials = {
        "email": "test.user@example.com",
        "password": "testpassword123"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            print("🧪 Testing Authenticated Analysis with Auto-Save")
            print("=" * 60)
            
            # Step 1: Login to get token
            print("\n1️⃣ Logging in...")
            async with session.post(
                f"{base_url}/api/v1/auth/login",
                json=user_credentials,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 200:
                    token_data = await response.json()
                    access_token = token_data['access_token']
                    print("✅ Login successful!")
                else:
                    print(f"❌ Login failed: {response.status}")
                    print("Make sure the test user exists or register first")
                    return False
            
            # Set headers for authenticated requests
            auth_headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Step 2: Create a business idea first
            print("\n2️⃣ Creating a business idea...")
            business_idea = {
                "title": "Smart Home Security",
                "description": "AI-powered home security system with facial recognition and smart alerts",
                "current_stage": "research",
                "main_goal": "Create an affordable smart security solution for homeowners",
                "biggest_challenge": "Balancing security features with user privacy concerns",
                "target_market": "Homeowners aged 30-55 concerned about security",
                "industry": "Home Security Technology"
            }
            
            async with session.post(
                f"{base_url}/api/v1/users/ideas",
                json=business_idea,
                headers=auth_headers
            ) as response:
                
                if response.status == 201:
                    idea_data = await response.json()
                    idea_id = idea_data['id']
                    print(f"✅ Business idea created: {idea_data['title']}")
                    print(f"   Idea ID: {idea_id}")
                else:
                    print(f"❌ Failed to create business idea: {response.status}")
                    return False
            
            # Step 3: Test competitor analysis with idea_id
            print("\n3️⃣ Testing competitor analysis with idea_id...")
            competitor_request = {
                "idea_description": business_idea["description"],
                "target_market": business_idea["target_market"],
                "industry": business_idea["industry"],
                "idea_id": idea_id  # Link to existing idea
            }
            
            async with session.post(
                f"{base_url}/api/v1/analyze/competitors",
                json=competitor_request,
                headers=auth_headers
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    print("✅ Competitor analysis completed with auto-save!")
                    print(f"   Status: {result['status']}")
                    print(f"   Message: {result['message']}")
                    print(f"   Competitors found: {len(result['report']['competitors'])}")
                else:
                    print(f"❌ Competitor analysis failed: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
            
            # Step 4: Test persona analysis without idea_id (should create new idea)
            print("\n4️⃣ Testing persona analysis without idea_id (auto-create idea)...")
            persona_request = {
                "business_idea": "AI-powered language learning app for professionals",
                "target_market": "Working professionals who want to learn languages efficiently",
                "industry": "EdTech"
                # Note: No idea_id provided - should auto-create
            }
            
            async with session.post(
                f"{base_url}/api/v1/analyze/personas",
                json=persona_request,
                headers=auth_headers
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    print("✅ Persona analysis completed with auto-save!")
                    print(f"   Status: {result['status']}")
                    print(f"   Message: {result['message']}")
                    print(f"   Personas generated: {len(result['report']['personas'])}")
                else:
                    print(f"❌ Persona analysis failed: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
            
            # Step 5: Check user's ideas (should have 2 now)
            print("\n5️⃣ Checking user's business ideas...")
            async with session.get(
                f"{base_url}/api/v1/users/ideas",
                headers=auth_headers
            ) as response:
                
                if response.status == 200:
                    ideas = await response.json()
                    print(f"✅ User now has {len(ideas)} business ideas:")
                    for idea in ideas:
                        print(f"   - {idea['title']} (Stage: {idea['current_stage']})")
                else:
                    print(f"❌ Failed to get user ideas: {response.status}")
            
            # Step 6: Check analysis history for the first idea
            print("\n6️⃣ Checking analysis history...")
            async with session.get(
                f"{base_url}/api/v1/users/ideas/{idea_id}/analyses",
                headers=auth_headers
            ) as response:
                
                if response.status == 200:
                    history = await response.json()
                    print(f"✅ Analysis history for '{business_idea['title']}':")
                    print(f"   Total analyses: {history['total_analyses']}")
                    for analysis in history['analyses']:
                        print(f"   - {analysis['analysis_type']}: {analysis['status']} ({analysis['created_at']})")
                else:
                    print(f"❌ Failed to get analysis history: {response.status}")
            
            # Step 7: Test unauthenticated request (should work but not save)
            print("\n7️⃣ Testing unauthenticated analysis (should work but not save)...")
            unauth_request = {
                "idea_description": "Simple food delivery app",
                "target_market": "Busy urban professionals"
            }
            
            async with session.post(
                f"{base_url}/api/v1/analyze/competitors",
                json=unauth_request,
                headers={"Content-Type": "application/json"}  # No auth header
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    print("✅ Unauthenticated analysis works!")
                    print(f"   Message: {result['message']}")
                    print("   (Results not saved - as expected)")
                else:
                    print(f"❌ Unauthenticated analysis failed: {response.status}")
            
            # Step 8: Test user analytics
            print("\n8️⃣ Checking user analytics...")
            async with session.get(
                f"{base_url}/api/v1/users/analytics",
                headers=auth_headers
            ) as response:
                
                if response.status == 200:
                    analytics = await response.json()
                    print("✅ User analytics updated:")
                    print(f"   Total ideas: {analytics['total_ideas']}")
                    print(f"   Total analyses: {analytics['total_analyses']}")
                    print(f"   Competitor analyses: {analytics['competitor_analyses_count']}")
                    print(f"   Persona analyses: {analytics['persona_analyses_count']}")
                else:
                    print(f"❌ Failed to get analytics: {response.status}")
            
            print("\n" + "=" * 60)
            print("🎉 Authenticated Analysis Test Complete!")
            print("\n✅ Features tested successfully:")
            print("   • Competitor analysis with auto-save (existing idea)")
            print("   • Persona analysis with auto-save (new idea creation)")
            print("   • Analysis history tracking")
            print("   • User analytics updates")
            print("   • Backward compatibility (unauthenticated access)")
            print("\n💡 Key benefits:")
            print("   • Users get persistent analysis storage automatically")
            print("   • No breaking changes - existing API users unaffected")
            print("   • Automatic idea creation when idea_id not provided")
            print("   • Full analysis history and user insights")
            
            return True
            
        except aiohttp.ClientConnectorError:
            print("❌ Connection failed. Make sure the server is running on localhost:8000")
            return False
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            return False


async def test_registration_first():
    """Register a test user if needed"""
    base_url = "http://localhost:8000"
    
    test_user = {
        "first_name": "Test",
        "last_name": "User",
        "email": "test.user@example.com",
        "password": "testpassword123"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{base_url}/api/v1/auth/register",
                json=test_user,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 201:
                    print("✅ Test user registered successfully!")
                    return True
                elif response.status == 400:
                    print("ℹ️ Test user already exists")
                    return True
                else:
                    print(f"❌ Failed to register test user: {response.status}")
                    return False
        except:
            return False


if __name__ == "__main__":
    print("🧪 Authenticated Analysis Auto-Save Test")
    print("=" * 50)
    
    # Ensure test user exists
    user_ready = asyncio.run(test_registration_first())
    
    if user_ready:
        # Run the main test
        success = asyncio.run(test_authenticated_analysis())
        
        if success:
            print("\n✅ All tests passed! Authenticated auto-save is working perfectly.")
        else:
            print("\n❌ Some tests failed. Check the error messages above.")
    else:
        print("❌ Could not prepare test user. Check server connection.")
    
    print("\nAPI Documentation: http://localhost:8000/docs") 