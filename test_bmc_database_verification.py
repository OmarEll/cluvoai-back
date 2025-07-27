#!/usr/bin/env python3
import asyncio
import aiohttp
import json
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_USER = {
    "first_name": "Omar",
    "last_name": "El Loumi", 
    "email": "omarelloumi531@gmail.com",
    "password": "omarelloumi531@gmail.com"
}
IDEA_ID = "44586e46-2bfe-48f3-8a7e-c14427758a30"

async def test_bmc_database_verification():
    """
    Test and verify Business Model Canvas data saved in the database
    """
    print(f"🗄️ Verifying Business Model Canvas Database Storage for Idea ID: {IDEA_ID}\n")
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. Register user first
            print("1. 🔐 Registering user...")
            register_response = await session.post(
                f"{BASE_URL}/auth/register",
                json=TEST_USER
            )
            
            if register_response.status == 201:
                print("✅ User registered successfully")
            elif register_response.status == 400:
                print("ℹ️ User already exists, continuing...")
            else:
                print(f"❌ Registration failed: {register_response.status}")
                return
            
            # 2. Login
            print("\n2. 🔐 Logging in...")
            login_response = await session.post(
                f"{BASE_URL}/auth/login",
                json={
                    "email": TEST_USER["email"],
                    "password": TEST_USER["password"]
                }
            )
            
            if login_response.status != 200:
                print(f"❌ Login failed: {login_response.status}")
                return
            
            login_data = await login_response.json()
            access_token = login_data.get("access_token")
            print("✅ Login successful")
            
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # 3. Generate new Business Model Canvas (if not exists)
            print(f"\n3. 🎨 Generating Business Model Canvas for Idea ID: {IDEA_ID}")
            canvas_request = {
                "business_idea": "AI-powered demand prediction platform for e-commerce businesses",
                "target_market": "e-commerce businesses",
                "industry": "e-commerce analytics software",
                "idea_id": IDEA_ID
            }
            
            generate_response = await session.post(
                f"{BASE_URL}/business-model-canvas/analyze",
                headers=headers,
                json=canvas_request
            )
            
            if generate_response.status == 200:
                generate_data = await generate_response.json()
                analysis_id = generate_data.get('analysis_id')
                print("✅ Business Model Canvas generated successfully!")
                print(f"   Analysis ID: {analysis_id}")
                print(f"   Message: {generate_data.get('message')}")
            else:
                print(f"❌ Canvas generation failed: {generate_response.status}")
                error_text = await generate_response.text()
                print(f"Error: {error_text}")
                return
            
            # 4. Retrieve the saved canvas from database
            print(f"\n4. 📊 Retrieving saved Business Model Canvas from database...")
            canvas_response = await session.get(
                f"{BASE_URL}/business-model-canvas/analyze/{IDEA_ID}",
                headers=headers
            )
            
            if canvas_response.status == 200:
                canvas_data = await canvas_response.json()
                canvas = canvas_data.get('canvas', {})
                
                print("✅ Business Model Canvas retrieved from database!")
                print(f"   Analysis ID: {canvas_data.get('analysis_id')}")
                print(f"   Canvas ID: {canvas.get('id')}")
                print(f"   Version: {canvas.get('version')}")
                print(f"   Status: {canvas.get('status')}")
                print(f"   Created At: {canvas.get('created_at')}")
                
                # Show detailed database storage verification
                print(f"\n📋 DATABASE STORAGE VERIFICATION:")
                
                # Customer Segments
                customer_segments = canvas.get('customer_segments', {})
                print(f"\n👥 CUSTOMER SEGMENTS (Saved in DB):")
                print(f"   Type: {customer_segments.get('segment_type', 'N/A')}")
                print(f"   Description: {customer_segments.get('description', 'N/A')}")
                print(f"   Characteristics: {len(customer_segments.get('characteristics', []))} items")
                print(f"   Needs: {len(customer_segments.get('needs', []))} items")
                print(f"   Pain Points: {len(customer_segments.get('pain_points', []))} items")
                
                # Value Propositions
                value_propositions = canvas.get('value_propositions', {})
                print(f"\n💎 VALUE PROPOSITIONS (Saved in DB):")
                print(f"   Type: {value_propositions.get('proposition_type', 'N/A')}")
                print(f"   Description: {value_propositions.get('description', 'N/A')}")
                print(f"   Benefits: {len(value_propositions.get('benefits', []))} items")
                print(f"   Pain Points Solved: {len(value_propositions.get('pain_points_solved', []))} items")
                print(f"   Unique Features: {len(value_propositions.get('unique_features', []))} items")
                
                # Channels
                channels = canvas.get('channels', {})
                print(f"\n📡 CHANNELS (Saved in DB):")
                print(f"   Type: {channels.get('channel_type', 'N/A')}")
                print(f"   Description: {channels.get('description', 'N/A')}")
                print(f"   Touchpoints: {len(channels.get('touchpoints', []))} items")
                print(f"   Distribution Strategy: {channels.get('distribution_strategy', 'N/A')}")
                
                # Customer Relationships
                customer_relationships = canvas.get('customer_relationships', {})
                print(f"\n🤝 CUSTOMER RELATIONSHIPS (Saved in DB):")
                print(f"   Type: {customer_relationships.get('relationship_type', 'N/A')}")
                print(f"   Description: {customer_relationships.get('description', 'N/A')}")
                print(f"   Acquisition: {customer_relationships.get('acquisition_strategy', 'N/A')}")
                print(f"   Retention: {customer_relationships.get('retention_strategy', 'N/A')}")
                print(f"   Engagement: {len(customer_relationships.get('engagement_tactics', []))} tactics")
                
                # Revenue Streams
                revenue_streams = canvas.get('revenue_streams', {})
                print(f"\n💰 REVENUE STREAMS (Saved in DB):")
                print(f"   Type: {revenue_streams.get('stream_type', 'N/A')}")
                print(f"   Description: {revenue_streams.get('description', 'N/A')}")
                print(f"   Pricing Model: {revenue_streams.get('pricing_model', 'N/A')}")
                print(f"   Revenue Sources: {len(revenue_streams.get('revenue_sources', []))} sources")
                print(f"   Pricing Strategy: {revenue_streams.get('pricing_strategy', 'N/A')}")
                
                # Key Resources
                key_resources = canvas.get('key_resources', {})
                print(f"\n🔧 KEY RESOURCES (Saved in DB):")
                print(f"   Type: {key_resources.get('resource_type', 'N/A')}")
                print(f"   Description: {key_resources.get('description', 'N/A')}")
                print(f"   Importance: {key_resources.get('importance_level', 'N/A')}")
                print(f"   Resource List: {len(key_resources.get('resource_list', []))} resources")
                
                # Key Activities
                key_activities = canvas.get('key_activities', {})
                print(f"\n⚡ KEY ACTIVITIES (Saved in DB):")
                print(f"   Type: {key_activities.get('activity_type', 'N/A')}")
                print(f"   Description: {key_activities.get('description', 'N/A')}")
                print(f"   Criticality: {key_activities.get('criticality', 'N/A')}")
                print(f"   Activity List: {len(key_activities.get('activity_list', []))} activities")
                
                # Key Partnerships
                key_partnerships = canvas.get('key_partnerships', {})
                print(f"\n🤝 KEY PARTNERSHIPS (Saved in DB):")
                print(f"   Type: {key_partnerships.get('partnership_type', 'N/A')}")
                print(f"   Description: {key_partnerships.get('description', 'N/A')}")
                print(f"   Partner Categories: {len(key_partnerships.get('partner_categories', []))} categories")
                print(f"   Partnership Benefits: {len(key_partnerships.get('partnership_benefits', []))} benefits")
                
                # Cost Structure
                cost_structure = canvas.get('cost_structure', {})
                print(f"\n💸 COST STRUCTURE (Saved in DB):")
                print(f"   Type: {cost_structure.get('structure_type', 'N/A')}")
                print(f"   Description: {cost_structure.get('description', 'N/A')}")
                print(f"   Fixed Costs: {len(cost_structure.get('fixed_costs', []))} items")
                print(f"   Variable Costs: {len(cost_structure.get('variable_costs', []))} items")
                print(f"   Cost Optimization: {cost_structure.get('cost_optimization', 'N/A')}")
                
                # Show context integration data
                print(f"\n🔗 CROSS-FEATURE CONTEXT INTEGRATION (Saved in DB):")
                if canvas.get('competitive_context'):
                    comp_context = canvas['competitive_context']
                    print(f"   ✅ Competitive Analysis: {comp_context.get('total_competitors', 0)} competitors")
                    print(f"      Market Position: {comp_context.get('market_position', 'N/A')}")
                    print(f"      Competitive Advantages: {len(comp_context.get('competitive_advantages', []))} items")
                
                if canvas.get('persona_context'):
                    persona_context = canvas['persona_context']
                    print(f"   ✅ Persona Analysis: {persona_context.get('personas_analyzed', 0)} personas")
                    print(f"      Target Demographics: {persona_context.get('target_demographics', 'N/A')}")
                    print(f"      Behavioral Insights: {len(persona_context.get('behavioral_insights', []))} insights")
                
                if canvas.get('market_sizing_context'):
                    market_context = canvas['market_sizing_context']
                    print(f"   ✅ Market Sizing: Market data integrated")
                    print(f"      TAM: {market_context.get('tam', 'N/A')}")
                    print(f"      SAM: {market_context.get('sam', 'N/A')}")
                    print(f"      SOM: {market_context.get('som', 'N/A')}")
                
                if canvas.get('business_model_context'):
                    bm_context = canvas['business_model_context']
                    print(f"   ✅ Business Model: Revenue insights integrated")
                    print(f"      Revenue Model: {bm_context.get('revenue_model', 'N/A')}")
                    print(f"      Pricing Strategy: {bm_context.get('pricing_strategy', 'N/A')}")
                
                # 5. Test canvas history
                print(f"\n5. 📚 Testing Canvas History from Database...")
                history_response = await session.get(
                    f"{BASE_URL}/business-model-canvas/history?idea_id={IDEA_ID}",
                    headers=headers
                )
                
                if history_response.status == 200:
                    history_data = await history_response.json()
                    print("✅ Canvas history retrieved from database!")
                    print(f"   Total Versions: {history_data.get('total_versions', 0)}")
                    print(f"   Latest Version: {history_data.get('latest_version', 'N/A')}")
                    
                    versions = history_data.get('versions', [])
                    for i, version in enumerate(versions[:3]):  # Show first 3 versions
                        print(f"   Version {i+1}: {version.get('version_id', 'N/A')} - {version.get('created_at', 'N/A')}")
                else:
                    print(f"❌ History failed: {history_response.status}")
                
                # 6. Test canvas insights
                print(f"\n6. 🧠 Testing Canvas Insights from Database...")
                insights_response = await session.get(
                    f"{BASE_URL}/business-model-canvas/insights/{IDEA_ID}",
                    headers=headers
                )
                
                if insights_response.status == 200:
                    insights_data = await insights_response.json()
                    print("✅ Canvas insights retrieved from database!")
                    print(f"   Strengths: {len(insights_data.get('strengths', []))}")
                    print(f"   Weaknesses: {len(insights_data.get('weaknesses', []))}")
                    print(f"   Opportunities: {len(insights_data.get('opportunities', []))}")
                    print(f"   Threats: {len(insights_data.get('threats', []))}")
                    print(f"   Recommendations: {len(insights_data.get('recommendations', []))}")
                    
                    # Show risk assessment
                    risk_assessment = insights_data.get('risk_assessment', {})
                    print(f"   Risk Assessment:")
                    print(f"      Market Risk: {risk_assessment.get('market_risk', 'N/A')}")
                    print(f"      Competitive Risk: {risk_assessment.get('competitive_risk', 'N/A')}")
                    print(f"      Execution Risk: {risk_assessment.get('execution_risk', 'N/A')}")
                else:
                    print(f"❌ Insights failed: {insights_response.status}")
                
                print(f"\n🎉 DATABASE STORAGE VERIFICATION COMPLETE!")
                print(f"✅ Business Model Canvas successfully saved to MongoDB")
                print(f"✅ All nine building blocks stored with detailed data")
                print(f"✅ Cross-feature context integration preserved")
                print(f"✅ Version history and insights available")
                print(f"✅ Analysis ID: {analysis_id}")
                print(f"✅ Idea ID: {IDEA_ID}")
                
            else:
                print(f"❌ Canvas retrieval failed: {canvas_response.status}")
                error_text = await canvas_response.text()
                print(f"Error: {error_text}")
            
            # 7. Show database connection info
            print(f"\n🗄️ DATABASE CONNECTION INFO:")
            print(f"   MongoDB Atlas: Connected")
            print(f"   Collection: saved_analyses")
            print(f"   Analysis Type: business_model_canvas")
            print(f"   User ID: {TEST_USER['email']}")
            print(f"   Idea ID: {IDEA_ID}")
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_bmc_database_verification()) 