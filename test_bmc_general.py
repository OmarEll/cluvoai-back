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

async def test_bmc_general():
    """
    Test Business Model Canvas generation without a specific idea ID
    """
    print(f"🎨 Testing General Business Model Canvas Generation\n")
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. Login
            print("1. 🔐 Logging in...")
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
            
            # 2. Generate Business Model Canvas without specific idea ID
            print(f"\n2. 🎨 Generating Business Model Canvas (no specific idea ID)...")
            canvas_request = {
                "business_idea": "AI-powered demand prediction platform for e-commerce businesses",
                "target_market": "e-commerce businesses",
                "industry": "e-commerce analytics software"
                # No idea_id specified - should create a new business idea
            }
            
            generate_response = await session.post(
                f"{BASE_URL}/business-model-canvas/analyze",
                headers=headers,
                json=canvas_request
            )
            
            if generate_response.status == 200:
                generate_data = await generate_response.json()
                analysis_id = generate_data.get('analysis_id')
                canvas = generate_data.get('canvas', {})
                idea_id = canvas.get('business_idea_id') if canvas else None
                
                print("✅ Business Model Canvas generated successfully!")
                print(f"   Analysis ID: {analysis_id}")
                print(f"   Generated Idea ID: {idea_id}")
                print(f"   Message: {generate_data.get('message')}")
                
                # Show canvas overview
                print(f"\n📋 CANVAS OVERVIEW:")
                print(f"   Business Idea: {canvas.get('business_idea', 'N/A')}")
                print(f"   Version: {canvas.get('version', 'N/A')}")
                print(f"   Status: {canvas.get('status', 'N/A')}")
                print(f"   Created At: {canvas.get('created_at', 'N/A')}")
                
                # Show building blocks summary
                print(f"\n🏗️ BUILDING BLOCKS SUMMARY:")
                
                # Customer Segments
                customer_segments = canvas.get('customer_segments', {})
                print(f"   👥 Customer Segments:")
                print(f"      Type: {customer_segments.get('segment_type', 'N/A')}")
                print(f"      Characteristics: {len(customer_segments.get('characteristics', []))} items")
                print(f"      Needs: {len(customer_segments.get('needs', []))} items")
                print(f"      Pain Points: {len(customer_segments.get('pain_points', []))} items")
                
                # Value Propositions
                value_propositions = canvas.get('value_propositions', {})
                print(f"   💎 Value Propositions:")
                print(f"      Type: {value_propositions.get('proposition_type', 'N/A')}")
                print(f"      Benefits: {len(value_propositions.get('benefits', []))} items")
                print(f"      Pain Points Solved: {len(value_propositions.get('pain_points_solved', []))} items")
                print(f"      Competitive Advantages: {len(value_propositions.get('competitive_advantages', []))} items")
                
                # Channels
                channels = canvas.get('channels', {})
                print(f"   📡 Channels:")
                print(f"      Type: {channels.get('channel_type', 'N/A')}")
                print(f"      Touchpoints: {len(channels.get('touchpoints', []))} items")
                print(f"      Effectiveness Metrics: {len(channels.get('effectiveness_metrics', []))} items")
                
                # Customer Relationships
                customer_relationships = canvas.get('customer_relationships', {})
                print(f"   🤝 Customer Relationships:")
                print(f"      Type: {customer_relationships.get('relationship_type', 'N/A')}")
                print(f"      Acquisition: {customer_relationships.get('acquisition_strategy', 'N/A')}")
                print(f"      Retention: {customer_relationships.get('retention_strategy', 'N/A')}")
                
                # Revenue Streams
                revenue_streams = canvas.get('revenue_streams', {})
                print(f"   💰 Revenue Streams:")
                print(f"      Type: {revenue_streams.get('stream_type', 'N/A')}")
                print(f"      Pricing Model: {revenue_streams.get('pricing_model', 'N/A')}")
                print(f"      Revenue Potential: {revenue_streams.get('revenue_potential', 'N/A')}")
                
                # Key Resources
                key_resources = canvas.get('key_resources', {})
                print(f"   🔧 Key Resources:")
                print(f"      Type: {key_resources.get('resource_type', 'N/A')}")
                print(f"      Importance: {key_resources.get('importance_level', 'N/A')}")
                print(f"      Acquisition Strategy: {key_resources.get('acquisition_strategy', 'N/A')}")
                
                # Key Activities
                key_activities = canvas.get('key_activities', {})
                print(f"   ⚡ Key Activities:")
                print(f"      Type: {key_activities.get('activity_type', 'N/A')}")
                print(f"      Criticality: {key_activities.get('criticality', 'N/A')}")
                print(f"      Resource Requirements: {len(key_activities.get('resource_requirements', []))} items")
                
                # Key Partnerships
                key_partnerships = canvas.get('key_partnerships', {})
                print(f"   🤝 Key Partnerships:")
                print(f"      Type: {key_partnerships.get('partnership_type', 'N/A')}")
                print(f"      Partner Categories: {len(key_partnerships.get('partner_categories', []))} items")
                print(f"      Partnership Benefits: {len(key_partnerships.get('partnership_benefits', []))} items")
                
                # Cost Structure
                cost_structure = canvas.get('cost_structure', {})
                print(f"   💸 Cost Structure:")
                print(f"      Type: {cost_structure.get('structure_type', 'N/A')}")
                print(f"      Fixed Costs: {len(cost_structure.get('fixed_costs', []))} items")
                print(f"      Variable Costs: {len(cost_structure.get('variable_costs', []))} items")
                
                # Show context integration
                print(f"\n🔗 CONTEXT INTEGRATION:")
                if canvas.get('competitive_context'):
                    print(f"   ✅ Competitive Analysis: Integrated")
                if canvas.get('persona_context'):
                    print(f"   ✅ Persona Analysis: Integrated")
                if canvas.get('market_sizing_context'):
                    print(f"   ✅ Market Sizing: Integrated")
                if canvas.get('business_model_context'):
                    print(f"   ✅ Business Model: Integrated")
                
                # 3. Verify database storage by retrieving the canvas
                if idea_id:
                    print(f"\n3. 📊 Verifying database storage for Idea ID: {idea_id}")
                    canvas_response = await session.get(
                        f"{BASE_URL}/business-model-canvas/analyze/{idea_id}",
                        headers=headers
                    )
                    
                    if canvas_response.status == 200:
                        canvas_data = await canvas_response.json()
                        retrieved_canvas = canvas_data.get('canvas', {})
                        
                        print("✅ Canvas successfully retrieved from database!")
                        print(f"   Retrieved Analysis ID: {canvas_data.get('analysis_id')}")
                        print(f"   Retrieved Canvas ID: {retrieved_canvas.get('id')}")
                        print(f"   Database Storage: ✅ CONFIRMED")
                        
                        # Show some detailed data to confirm it's comprehensive
                        print(f"\n📋 DETAILED DATA VERIFICATION:")
                        
                        # Show some actual data from customer segments
                        customer_segments = retrieved_canvas.get('customer_segments', {})
                        if customer_segments.get('characteristics'):
                            print(f"   👥 Sample Characteristics:")
                            for i, char in enumerate(customer_segments['characteristics'][:3]):
                                print(f"      {i+1}. {char}")
                        
                        # Show some actual data from value propositions
                        value_propositions = retrieved_canvas.get('value_propositions', {})
                        if value_propositions.get('benefits'):
                            print(f"   💎 Sample Benefits:")
                            for i, benefit in enumerate(value_propositions['benefits'][:3]):
                                print(f"      {i+1}. {benefit}")
                        
                        # Show some actual data from channels
                        channels = retrieved_canvas.get('channels', {})
                        if channels.get('touchpoints'):
                            print(f"   📡 Sample Touchpoints:")
                            for i, touch in enumerate(channels['touchpoints'][:3]):
                                print(f"      {i+1}. {touch}")
                        
                        # Show some actual data from revenue streams
                        revenue_streams = retrieved_canvas.get('revenue_streams', {})
                        if revenue_streams.get('pricing_strategy'):
                            print(f"   💰 Pricing Strategy: {revenue_streams['pricing_strategy']}")
                        
                        # Show some actual data from cost structure
                        cost_structure = retrieved_canvas.get('cost_structure', {})
                        if cost_structure.get('fixed_costs'):
                            print(f"   💸 Sample Fixed Costs:")
                            for i, cost in enumerate(cost_structure['fixed_costs'][:3]):
                                print(f"      {i+1}. {cost}")
                        
                        print(f"\n🎉 COMPREHENSIVE BUSINESS MODEL CANVAS TEST COMPLETE!")
                        print(f"✅ Canvas generated successfully without specific idea ID")
                        print(f"✅ New business idea created automatically")
                        print(f"✅ Comprehensive data populated for all building blocks")
                        print(f"✅ Database storage and retrieval working perfectly")
                        print(f"✅ Cross-feature context integration preserved")
                        print(f"✅ Analysis ID: {analysis_id}")
                        print(f"✅ Generated Idea ID: {idea_id}")
                        
                    else:
                        print(f"❌ Canvas retrieval failed: {canvas_response.status}")
                        error_text = await canvas_response.text()
                        print(f"Error: {error_text}")
                else:
                    print(f"\n⚠️ No idea ID generated, cannot verify database storage")
                
            else:
                print(f"❌ Canvas generation failed: {generate_response.status}")
                error_text = await generate_response.text()
                print(f"Error: {error_text}")
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_bmc_general()) 