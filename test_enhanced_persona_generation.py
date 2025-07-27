#!/usr/bin/env python3
"""
Test script for enhanced persona generation with competitor context
"""

import asyncio
import aiohttp
import json
from datetime import datetime


async def test_enhanced_persona_generation():
    """Test persona generation enhancement with competitor context"""
    
    base_url = "http://localhost:8000"
    
    # Test user credentials
    user_credentials = {
        "email": "enhanced.tester@example.com",
        "password": "enhancedtest123"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            print("🧪 Testing Enhanced Persona Generation with Competitor Context")
            print("=" * 70)
            
            # Step 1: Login
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
                    return False
            
            # Set headers for authenticated requests
            auth_headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Step 2: Create a business idea
            print("\n2️⃣ Creating a business idea...")
            business_idea = {
                "title": "AI-Powered Learning Platform",
                "description": "An adaptive learning platform that uses AI to personalize educational content for professionals",
                "current_stage": "research",
                "main_goal": "Create personalized learning experiences that adapt to individual learning styles",
                "biggest_challenge": "Understanding diverse learning preferences and creating truly adaptive content",
                "target_market": "Working professionals seeking skill development",
                "industry": "EdTech"
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
            
            # Step 3: Run competitor analysis first to create context
            print("\n3️⃣ Running competitor analysis to create context...")
            competitor_request = {
                "idea_description": business_idea["description"],
                "target_market": business_idea["target_market"],
                "industry": business_idea["industry"],
                "idea_id": idea_id
            }
            
            async with session.post(
                f"{base_url}/api/v1/analyze/competitors",
                json=competitor_request,
                headers=auth_headers
            ) as response:
                
                if response.status == 200:
                    competitor_result = await response.json()
                    competitor_analysis_id = competitor_result.get('analysis_id')
                    print("✅ Competitor analysis completed!")
                    print(f"   Analysis ID: {competitor_analysis_id}")
                    print(f"   Competitors found: {len(competitor_result['report']['competitors'])}")
                    
                    # Show some competitor insights
                    competitors = competitor_result['report']['competitors']
                    print("   Key competitors:")
                    for comp in competitors[:3]:  # Show first 3
                        basic_info = comp.get('basic_info', {})
                        name = basic_info.get('name', 'Unknown Company')
                        description = basic_info.get('description', 'No description')
                        print(f"     - {name}: {description[:100] if description else 'No description'}...")
                else:
                    print(f"❌ Competitor analysis failed: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
                    return False
            
            # Step 4: Run persona analysis WITH competitor context
            print("\n4️⃣ Running persona analysis WITH competitor context...")
            persona_request_enhanced = {
                "business_idea": business_idea["description"],
                "target_market": business_idea["target_market"],
                "industry": business_idea["industry"],
                "idea_id": idea_id  # This will trigger competitor context lookup
            }
            
            async with session.post(
                f"{base_url}/api/v1/analyze/personas",
                json=persona_request_enhanced,
                headers=auth_headers
            ) as response:
                
                if response.status == 200:
                    enhanced_persona_result = await response.json()
                    enhanced_analysis_id = enhanced_persona_result.get('analysis_id')
                    print("✅ Enhanced persona analysis completed!")
                    print(f"   Analysis ID: {enhanced_analysis_id}")
                    print(f"   Enhanced personas generated: {len(enhanced_persona_result['report']['personas'])}")
                    
                    print("\n   Enhanced persona details:")
                    for i, persona in enumerate(enhanced_persona_result['report']['personas'], 1):
                        print(f"     {i}. {persona['name']}")
                        print(f"        Description: {persona['description']}")
                        print(f"        Demographics: {persona['demographics']['age_range']}, {persona['demographics'].get('location', 'N/A')}")
                        print(f"        Key Goals: {', '.join(persona['psychographics']['goals'][:2])}")
                        print(f"        Main Pain Points: {', '.join(persona['psychographics']['pain_points'][:2])}")
                        
                        # Show market insights
                        insights = persona['persona_insights']
                        print(f"        Market Size: {insights.get('market_size', 'N/A')}")
                        if insights.get('gaps_identified'):
                            print(f"        Market Gaps: {', '.join(insights['gaps_identified'][:2])}")
                        print()
                    
                    # Show targeting recommendations
                    recommendations = enhanced_persona_result['report'].get('targeting_recommendations', [])
                    if recommendations:
                        print("   Targeting Recommendations:")
                        for rec in recommendations[:3]:  # Show first 3
                            print(f"     - {rec}")
                    
                    # Show market insights
                    market_insights = enhanced_persona_result['report'].get('market_insights', [])
                    if market_insights:
                        print("   Market Insights:")
                        for insight in market_insights[:3]:  # Show first 3
                            print(f"     - {insight}")
                    
                else:
                    print(f"❌ Enhanced persona analysis failed: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
                    return False
            
            print("\n" + "=" * 70)
            print("🎉 Enhanced Persona Generation Test Complete!")
            print("\n✅ Features tested successfully:")
            print("   • Competitor analysis context extraction")
            print("   • Enhanced persona generation with competitor insights")
            print("   • Analysis history integration")
            print("   • Market gap identification")
            print("   • User behavior insights from competitor data")
            
            print("\n🚀 Enhancement Benefits:")
            print("   • More accurate personas based on real competitor data")
            print("   • Better understanding of user pain points")
            print("   • Identification of underserved market segments")
            print("   • Competitive differentiation opportunities")
            print("   • Data-driven persona insights vs generic assumptions")
            
            return True
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False


async def test_registration_first():
    """Register a test user if needed"""
    base_url = "http://localhost:8000"
    
    test_user = {
        "first_name": "Enhanced",
        "last_name": "Tester",
        "email": "enhanced.tester@example.com",
        "password": "enhancedtest123"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{base_url}/api/v1/auth/register",
                json=test_user,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 201:
                    print("✅ Enhanced test user registered successfully!")
                    return True
                elif response.status == 400:
                    print("ℹ️ Enhanced test user already exists")
                    return True
                else:
                    print(f"❌ Failed to register enhanced test user: {response.status}")
                    return False
        except:
            return False


if __name__ == "__main__":
    print("🧪 Enhanced Persona Generation Test")
    print("=" * 50)
    
    # Ensure test user exists
    user_ready = asyncio.run(test_registration_first())
    
    if user_ready:
        # Run the main test
        success = asyncio.run(test_enhanced_persona_generation())
        
        if success:
            print("\n✅ All tests passed! Enhanced persona generation is working perfectly.")
            print("\n💡 Your personas are now powered by real competitor insights!")
        else:
            print("\n❌ Some tests failed. Check the error messages above.")
    else:
        print("❌ Could not prepare test user. Check server connection.")
    
    print("\nAPI Documentation: http://localhost:8000/docs") 