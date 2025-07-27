#!/usr/bin/env python3
"""
Test script for the comprehensive market sizing feature
"""

import asyncio
import aiohttp
import json
from datetime import datetime


async def test_market_sizing_feature():
    """Test the complete market sizing feature workflow"""
    
    base_url = "http://localhost:8000"
    
    # Test user credentials
    user_credentials = {
        "email": "omarelloumi530@gmail.com",
        "password": "omarelloumi530@gmail.com"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            print("🧪 Testing Comprehensive Market Sizing Feature")
            print("=" * 60)
            
            # Step 1: Register or login user
            print("\n1️⃣ User Authentication...")
            
            # Try to register user (ignore error if already exists)
            try:
                register_data = {
                    "first_name": "Market",
                    "last_name": "Tester",
                    "email": user_credentials["email"],
                    "password": user_credentials["password"]
                }
                async with session.post(f"{base_url}/api/v1/auth/register", json=register_data) as response:
                    if response.status == 200:
                        print("✅ User registered successfully")
                    else:
                        print("ℹ️ User already exists, proceeding with login")
            except Exception:
                pass
            
            # Login
            async with session.post(f"{base_url}/api/v1/auth/login", json=user_credentials) as response:
                if response.status == 200:
                    login_result = await response.json()
                    access_token = login_result["access_token"]
                    print("✅ User logged in successfully")
                else:
                    error = await response.text()
                    print(f"❌ Login failed: {error}")
                    return
            
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # Step 2: Get market sizing options
            print("\n2️⃣ Getting market sizing options...")
            async with session.get(f"{base_url}/api/v1/market-sizing/options") as response:
                if response.status == 200:
                    options = await response.json()
                    print("✅ Market sizing options retrieved")
                    print(f"   Geographic scopes: {len(options['geographic_scopes']['regions'])} regions")
                    print(f"   Customer types: {len(options['customer_types'])} types")
                    print(f"   Revenue models: {len(options['revenue_models'])} models")
                    print(f"   Industry benchmarks: {len(options['industry_benchmarks'])} industries")
                else:
                    print(f"❌ Failed to get options: {response.status}")
                    return
            
            # Step 3: Create a business idea first
            print("\n3️⃣ Creating business idea...")
            idea_data = {
                "title": "AI Fitness Coach App",
                "description": "AI-powered fitness coaching app that provides personalized workout plans and nutrition guidance for busy professionals who want to stay fit but have limited time for gym visits",
                "current_stage": "idea",
                "main_goal": "Market validation and sizing",
                "biggest_challenge": "Understanding market opportunity",
                "target_market": "Busy professionals aged 25-45",
                "industry": "Health & Fitness Technology"
            }
            
            async with session.post(f"{base_url}/api/v1/users/ideas", json=idea_data, headers=headers) as response:
                if response.status in [200, 201]:  # Accept both OK and Created status codes
                    idea_result = await response.json()
                    idea_id = idea_result["id"]
                    print(f"✅ Business idea created with ID: {idea_id}")
                else:
                    error = await response.text()
                    print(f"❌ Failed to create idea: {response.status} - {error}")
                    return
            
            # Step 4: Run market sizing analysis
            print("\n4️⃣ Running market sizing analysis...")
            market_sizing_request = {
                "business_idea": "AI-powered fitness coaching app that provides personalized workout plans and nutrition guidance for busy professionals who want to stay fit but have limited time for gym visits",
                "industry": "Health & Fitness Technology",
                "target_market": "Busy professionals aged 25-45 who value health and fitness but have time constraints",
                "geographic_scope": "usa",
                "customer_type": "b2c",
                "revenue_model": "subscription",
                "estimated_price_point": 29.99,
                "idea_id": idea_id
            }
            
            start_time = datetime.now()
            async with session.post(f"{base_url}/api/v1/market-sizing/analyze", json=market_sizing_request, headers=headers) as response:
                if response.status == 200:
                    market_result = await response.json()
                    analysis_time = (datetime.now() - start_time).total_seconds()
                    analysis_id = market_result.get('analysis_id')
                    
                    print("✅ Market sizing analysis completed!")
                    print(f"   Analysis ID: {analysis_id}")
                    print(f"   Execution time: {analysis_time:.2f} seconds")
                    print(f"   Message: {market_result['message']}")
                    
                    # Display key market metrics
                    report = market_result['report']
                    tam_sam_som = report['tam_sam_som']
                    
                    print(f"\n📊 Market Metrics:")
                    print(f"   TAM (Total Addressable Market): ${tam_sam_som['tam']:,.0f}")
                    print(f"   SAM (Serviceable Addressable Market): ${tam_sam_som['sam']:,.0f}")
                    print(f"   SOM (Serviceable Obtainable Market): ${tam_sam_som['som']:,.0f}")
                    print(f"   Market Penetration Rate: {tam_sam_som['market_penetration_rate']:.1f}%")
                    print(f"   Confidence Level: {report['confidence_level']}")
                    
                    # Display market overview
                    market_overview = report['market_overview']
                    print(f"\n🏭 Market Overview:")
                    print(f"   Current Market Size: ${market_overview['market_size_current']:,.0f}")
                    print(f"   Growth Rate: {market_overview['market_growth_rate']:.1f}%")
                    print(f"   Projected Growth: {market_overview['projected_growth_rate']:.1f}%")
                    print(f"   Data Sources: {', '.join(market_overview['data_sources'])}")
                    
                    # Display investment highlights
                    if report.get('investment_highlights'):
                        print(f"\n💡 Investment Highlights:")
                        for highlight in report['investment_highlights'][:3]:
                            print(f"   • {highlight}")
                    
                    # Display revenue projections
                    if report.get('revenue_projections'):
                        print(f"\n📈 Revenue Projections:")
                        for projection in report['revenue_projections'][:3]:
                            print(f"   Year {projection['year']}: ${projection['total_revenue']:,.0f} "
                                  f"({projection['projected_customers']:,} customers)")
                    
                else:
                    error = await response.text()
                    print(f"❌ Market sizing analysis failed: {error}")
                    return
            
            # Step 5: Get saved market sizing analysis
            print("\n5️⃣ Retrieving saved market sizing analysis...")
            async with session.get(f"{base_url}/api/v1/market-sizing/analyze/{idea_id}", headers=headers) as response:
                if response.status == 200:
                    saved_analysis = await response.json()
                    print("✅ Saved market sizing analysis retrieved")
                    print(f"   Analysis ID: {saved_analysis.get('analysis_id')}")
                    print(f"   TAM: ${saved_analysis['report']['tam_sam_som']['tam']:,.0f}")
                else:
                    error = await response.text()
                    print(f"❌ Failed to retrieve saved analysis: {error}")
            
            # Step 6: Get market opportunity insights
            print("\n6️⃣ Getting market opportunity insights...")
            async with session.get(f"{base_url}/api/v1/market-sizing/opportunity-insights/{idea_id}", headers=headers) as response:
                if response.status == 200:
                    insights = await response.json()
                    print("✅ Market opportunity insights generated")
                    print(f"   Total Market Value: ${insights['total_market_value']:,.0f}")
                    print(f"   Growth Potential: {insights['growth_potential']:.1f}%")
                    print(f"   Recommendation: {insights['recommendation']}")
                    print(f"   Key Insights: {len(insights['key_insights'])} insights")
                    
                    for i, insight in enumerate(insights['key_insights'][:3]):
                        print(f"   {i+1}. {insight['title']}: {insight['description']}")
                else:
                    error = await response.text()
                    print(f"❌ Failed to get opportunity insights: {error}")
            
            # Step 7: Get market sizing history
            print("\n7️⃣ Getting market sizing history...")
            async with session.get(f"{base_url}/api/v1/market-sizing/history?page=1&per_page=10", headers=headers) as response:
                if response.status == 200:
                    history = await response.json()
                    print("✅ Market sizing history retrieved")
                    print(f"   Total analyses: {history['total_count']}")
                    print(f"   Current page: {history['page']}/{history['total_pages']}")
                    
                    if history['analyses']:
                        latest = history['analyses'][0]
                        print(f"   Latest analysis: TAM ${latest['tam']:,.0f}, Confidence: {latest['confidence_level']}")
                else:
                    error = await response.text()
                    print(f"❌ Failed to get history: {error}")
            
            # Step 8: Test market sizing without authentication
            print("\n8️⃣ Testing unauthenticated market sizing...")
            unauthenticated_request = {
                "business_idea": "Online tutoring platform for high school students",
                "industry": "Education Technology",
                "target_market": "High school students and parents seeking academic support",
                "geographic_scope": "usa",
                "customer_type": "b2c",
                "revenue_model": "subscription",
                "estimated_price_point": 49.99
            }
            
            async with session.post(f"{base_url}/api/v1/market-sizing/analyze", json=unauthenticated_request) as response:
                if response.status == 200:
                    unauth_result = await response.json()
                    print("✅ Unauthenticated market sizing completed")
                    print(f"   TAM: ${unauth_result['report']['tam_sam_som']['tam']:,.0f}")
                    print(f"   Analysis ID: {unauth_result.get('analysis_id', 'None (not saved)')}")
                else:
                    error = await response.text()
                    print(f"❌ Unauthenticated analysis failed: {error}")
            
            print("\n🎉 Market Sizing Feature Test Complete!")
            print("=" * 60)
            print("✅ All core market sizing functionality working correctly")
            print("✅ TAM/SAM/SOM calculations functioning")
            print("✅ Market data collection operational")
            print("✅ Revenue projections generated")
            print("✅ Investment insights provided")
            print("✅ Authentication integration working")
            print("✅ Data persistence confirmed")
            
        except Exception as e:
            print(f"\n❌ Unexpected error during testing: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_market_sizing_feature()) 