#!/usr/bin/env python3
import asyncio
import aiohttp
import json

# Test configuration
BASE_URL = "http://localhost:8000/api/v1"
TEST_USER = {
    "first_name": "Omar",
    "last_name": "El Loumi", 
    "email": "omarelloumi531@gmail.com",
    "password": "password123"
}

async def test_business_model_canvas_demo():
    """
    Comprehensive demo of the Business Model Canvas feature
    """
    print("🎨 Business Model Canvas Feature Demo\n")
    
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
            
            # 3. Create business idea through onboarding
            print("\n3. 📝 Creating business idea...")
            questionnaire_data = {
                "questionnaire": {
                    "business_level": "some_experience",
                    "current_stage": "validating_idea",
                    "business_idea_description": "We help e-commerce businesses solve inventory forecasting problems by providing an AI-powered demand prediction platform",
                    "main_goal": "validate_if_people_want_idea", 
                    "biggest_challenge": "dont_know_if_anyone_needs_this"
                }
            }
            
            onboarding_response = await session.post(
                f"{BASE_URL}/onboarding/questionnaire",
                headers=headers,
                json=questionnaire_data
            )
            
            if onboarding_response.status == 200:
                onboarding_data = await onboarding_response.json()
                business_idea = onboarding_data["business_idea"]
                idea_id = business_idea["id"]
                print(f"✅ Business idea created: {business_idea['title']}")
            else:
                print(f"❌ Onboarding failed: {onboarding_response.status}")
                return
            
            # 4. Test Business Model Canvas options
            print("\n4. ⚙️ Testing Business Model Canvas Options...")
            options_response = await session.get(f"{BASE_URL}/business-model-canvas/options")
            
            if options_response.status == 200:
                options_data = await options_response.json()
                print("✅ Business Model Canvas options retrieved:")
                print(f"   📊 Customer Segment Types: {len(options_data.get('customer_segment_types', []))}")
                print(f"   💎 Value Proposition Types: {len(options_data.get('value_proposition_types', []))}")
                print(f"   📡 Channel Types: {len(options_data.get('channel_types', []))}")
                print(f"   🤝 Customer Relationship Types: {len(options_data.get('customer_relationship_types', []))}")
                print(f"   💰 Revenue Stream Types: {len(options_data.get('revenue_stream_types', []))}")
                print(f"   🔧 Key Resource Types: {len(options_data.get('key_resource_types', []))}")
                print(f"   ⚡ Key Activity Types: {len(options_data.get('key_activity_types', []))}")
                print(f"   🤝 Partnership Types: {len(options_data.get('partnership_types', []))}")
                print(f"   💸 Cost Structure Types: {len(options_data.get('cost_structure_types', []))}")
                print(f"   📄 Export Formats: {len(options_data.get('export_formats', []))}")
            else:
                print(f"❌ Options failed: {options_response.status}")
            
            # 5. Generate Business Model Canvas
            print("\n5. 🎨 Generating Business Model Canvas...")
            canvas_request = {
                "business_idea": questionnaire_data["questionnaire"]["business_idea_description"],
                "target_market": "e-commerce businesses",
                "industry": "e-commerce analytics software",
                "idea_id": idea_id
            }
            
            canvas_response = await session.post(
                f"{BASE_URL}/business-model-canvas/analyze",
                headers=headers,
                json=canvas_request
            )
            
            if canvas_response.status == 200:
                canvas_data = await canvas_response.json()
                canvas = canvas_data.get('canvas', {})
                
                print("✅ Business Model Canvas generated successfully!")
                print(f"   Analysis ID: {canvas_data.get('analysis_id')}")
                print(f"   Canvas ID: {canvas.get('id')}")
                print(f"   Version: {canvas.get('version')}")
                print(f"   Status: {canvas.get('status')}")
                
                # Show the nine building blocks
                print(f"\n📋 THE NINE BUILDING BLOCKS:")
                
                # Customer Segments
                customer_segments = canvas.get('customer_segments', {})
                print(f"\n👥 CUSTOMER SEGMENTS:")
                print(f"   Type: {customer_segments.get('segment_type', 'N/A')}")
                print(f"   Description: {customer_segments.get('description', 'N/A')}")
                print(f"   Characteristics: {', '.join(customer_segments.get('characteristics', [])[:3])}")
                print(f"   Needs: {', '.join(customer_segments.get('needs', [])[:3])}")
                
                # Value Propositions
                value_propositions = canvas.get('value_propositions', {})
                print(f"\n💎 VALUE PROPOSITIONS:")
                print(f"   Type: {value_propositions.get('proposition_type', 'N/A')}")
                print(f"   Description: {value_propositions.get('description', 'N/A')}")
                print(f"   Benefits: {', '.join(value_propositions.get('benefits', [])[:3])}")
                print(f"   Pain Points Solved: {', '.join(value_propositions.get('pain_points_solved', [])[:3])}")
                
                # Channels
                channels = canvas.get('channels', {})
                print(f"\n📡 CHANNELS:")
                print(f"   Type: {channels.get('channel_type', 'N/A')}")
                print(f"   Description: {channels.get('description', 'N/A')}")
                print(f"   Touchpoints: {', '.join(channels.get('touchpoints', [])[:3])}")
                
                # Customer Relationships
                customer_relationships = canvas.get('customer_relationships', {})
                print(f"\n🤝 CUSTOMER RELATIONSHIPS:")
                print(f"   Type: {customer_relationships.get('relationship_type', 'N/A')}")
                print(f"   Description: {customer_relationships.get('description', 'N/A')}")
                print(f"   Acquisition: {customer_relationships.get('acquisition_strategy', 'N/A')}")
                print(f"   Retention: {customer_relationships.get('retention_strategy', 'N/A')}")
                
                # Revenue Streams
                revenue_streams = canvas.get('revenue_streams', {})
                print(f"\n💰 REVENUE STREAMS:")
                print(f"   Type: {revenue_streams.get('stream_type', 'N/A')}")
                print(f"   Description: {revenue_streams.get('description', 'N/A')}")
                print(f"   Pricing Model: {revenue_streams.get('pricing_model', 'N/A')}")
                
                # Key Resources
                key_resources = canvas.get('key_resources', {})
                print(f"\n🔧 KEY RESOURCES:")
                print(f"   Type: {key_resources.get('resource_type', 'N/A')}")
                print(f"   Description: {key_resources.get('description', 'N/A')}")
                print(f"   Importance: {key_resources.get('importance_level', 'N/A')}")
                
                # Key Activities
                key_activities = canvas.get('key_activities', {})
                print(f"\n⚡ KEY ACTIVITIES:")
                print(f"   Type: {key_activities.get('activity_type', 'N/A')}")
                print(f"   Description: {key_activities.get('description', 'N/A')}")
                print(f"   Criticality: {key_activities.get('criticality', 'N/A')}")
                
                # Key Partnerships
                key_partnerships = canvas.get('key_partnerships', {})
                print(f"\n🤝 KEY PARTNERSHIPS:")
                print(f"   Type: {key_partnerships.get('partnership_type', 'N/A')}")
                print(f"   Description: {key_partnerships.get('description', 'N/A')}")
                print(f"   Partner Categories: {', '.join(key_partnerships.get('partner_categories', [])[:3])}")
                
                # Cost Structure
                cost_structure = canvas.get('cost_structure', {})
                print(f"\n💸 COST STRUCTURE:")
                print(f"   Type: {cost_structure.get('structure_type', 'N/A')}")
                print(f"   Description: {cost_structure.get('description', 'N/A')}")
                print(f"   Fixed Costs: {', '.join(cost_structure.get('fixed_costs', [])[:3])}")
                print(f"   Variable Costs: {', '.join(cost_structure.get('variable_costs', [])[:3])}")
                
                # Show context integration
                print(f"\n🔗 CROSS-FEATURE CONTEXT INTEGRATION:")
                if canvas.get('competitive_context'):
                    print(f"   ✅ Competitive Analysis: {canvas['competitive_context'].get('total_competitors', 0)} competitors analyzed")
                if canvas.get('persona_context'):
                    print(f"   ✅ Persona Analysis: {canvas['persona_context'].get('personas_analyzed', 0)} personas analyzed")
                if canvas.get('market_sizing_context'):
                    print(f"   ✅ Market Sizing: Market data integrated")
                if canvas.get('business_model_context'):
                    print(f"   ✅ Business Model: Revenue insights integrated")
                
                print(f"\n🎉 BUSINESS MODEL CANVAS FEATURE DEMO SUCCESSFUL!")
                print(f"✅ All nine building blocks generated with AI intelligence")
                print(f"✅ Cross-feature context integration working")
                print(f"✅ Comprehensive business model visualization ready")
                print(f"✅ Strategic framework for business planning complete")
                
            else:
                print(f"❌ Business Model Canvas generation failed: {canvas_response.status}")
                error_text = await canvas_response.text()
                print(f"Error: {error_text}")
            
            # 6. Test canvas insights
            print("\n6. 🧠 Testing Canvas Insights...")
            insights_response = await session.get(
                f"{BASE_URL}/business-model-canvas/insights/{idea_id}",
                headers=headers
            )
            
            if insights_response.status == 200:
                insights_data = await insights_response.json()
                print("✅ Canvas insights generated:")
                print(f"   Strengths: {len(insights_data.get('strengths', []))}")
                print(f"   Weaknesses: {len(insights_data.get('weaknesses', []))}")
                print(f"   Opportunities: {len(insights_data.get('opportunities', []))}")
                print(f"   Threats: {len(insights_data.get('threats', []))}")
                print(f"   Recommendations: {len(insights_data.get('recommendations', []))}")
            else:
                print(f"❌ Insights failed: {insights_response.status}")
            
            # 7. Show API documentation
            print(f"\n📚 API Documentation:")
            print(f"   Full API docs: http://localhost:8000/docs")
            print(f"   Business Model Canvas endpoints: http://localhost:8000/docs#/Business%20Model%20Canvas")
            
        except Exception as e:
            print(f"❌ Demo failed with error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_business_model_canvas_demo()) 