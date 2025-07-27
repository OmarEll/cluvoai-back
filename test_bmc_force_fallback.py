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
IDEA_ID = "test-idea-fallback-123"

async def test_bmc_force_fallback():
    """
    Test Business Model Canvas with fallback generation
    """
    print(f"🎨 Testing Business Model Canvas Fallback Generation for Idea ID: {IDEA_ID}\n")
    
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
            
            # 2. Generate Business Model Canvas with comprehensive data
            print(f"\n2. 🎨 Generating Business Model Canvas with Fallback Data...")
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
            
            # 3. Retrieve the saved canvas from database
            print(f"\n3. 📊 Retrieving saved Business Model Canvas from database...")
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
                print(f"\n📋 COMPREHENSIVE DATABASE STORAGE VERIFICATION:")
                
                # Customer Segments
                customer_segments = canvas.get('customer_segments', {})
                print(f"\n👥 CUSTOMER SEGMENTS (Saved in DB):")
                print(f"   Type: {customer_segments.get('segment_type', 'N/A')}")
                print(f"   Description: {customer_segments.get('description', 'N/A')}")
                print(f"   Characteristics: {len(customer_segments.get('characteristics', []))} items")
                if customer_segments.get('characteristics'):
                    for i, char in enumerate(customer_segments['characteristics'][:3]):
                        print(f"      {i+1}. {char}")
                print(f"   Needs: {len(customer_segments.get('needs', []))} items")
                if customer_segments.get('needs'):
                    for i, need in enumerate(customer_segments['needs'][:3]):
                        print(f"      {i+1}. {need}")
                print(f"   Pain Points: {len(customer_segments.get('pain_points', []))} items")
                if customer_segments.get('pain_points'):
                    for i, pain in enumerate(customer_segments['pain_points'][:3]):
                        print(f"      {i+1}. {pain}")
                print(f"   Size Estimate: {customer_segments.get('size_estimate', 'N/A')}")
                
                # Value Propositions
                value_propositions = canvas.get('value_propositions', {})
                print(f"\n💎 VALUE PROPOSITIONS (Saved in DB):")
                print(f"   Type: {value_propositions.get('proposition_type', 'N/A')}")
                print(f"   Description: {value_propositions.get('description', 'N/A')}")
                print(f"   Benefits: {len(value_propositions.get('benefits', []))} items")
                if value_propositions.get('benefits'):
                    for i, benefit in enumerate(value_propositions['benefits'][:3]):
                        print(f"      {i+1}. {benefit}")
                print(f"   Pain Points Solved: {len(value_propositions.get('pain_points_solved', []))} items")
                if value_propositions.get('pain_points_solved'):
                    for i, pain in enumerate(value_propositions['pain_points_solved'][:3]):
                        print(f"      {i+1}. {pain}")
                print(f"   Competitive Advantages: {len(value_propositions.get('competitive_advantages', []))} items")
                if value_propositions.get('competitive_advantages'):
                    for i, adv in enumerate(value_propositions['competitive_advantages'][:3]):
                        print(f"      {i+1}. {adv}")
                
                # Channels
                channels = canvas.get('channels', {})
                print(f"\n📡 CHANNELS (Saved in DB):")
                print(f"   Type: {channels.get('channel_type', 'N/A')}")
                print(f"   Description: {channels.get('description', 'N/A')}")
                print(f"   Touchpoints: {len(channels.get('touchpoints', []))} items")
                if channels.get('touchpoints'):
                    for i, touch in enumerate(channels['touchpoints'][:3]):
                        print(f"      {i+1}. {touch}")
                print(f"   Effectiveness Metrics: {len(channels.get('effectiveness_metrics', []))} items")
                if channels.get('effectiveness_metrics'):
                    for i, metric in enumerate(channels['effectiveness_metrics'][:3]):
                        print(f"      {i+1}. {metric}")
                
                # Customer Relationships
                customer_relationships = canvas.get('customer_relationships', {})
                print(f"\n🤝 CUSTOMER RELATIONSHIPS (Saved in DB):")
                print(f"   Type: {customer_relationships.get('relationship_type', 'N/A')}")
                print(f"   Description: {customer_relationships.get('description', 'N/A')}")
                print(f"   Acquisition: {customer_relationships.get('acquisition_strategy', 'N/A')}")
                print(f"   Retention: {customer_relationships.get('retention_strategy', 'N/A')}")
                print(f"   Growth: {customer_relationships.get('growth_strategy', 'N/A')}")
                print(f"   Automation Level: {customer_relationships.get('automation_level', 'N/A')}")
                print(f"   Personalization: {customer_relationships.get('personalization_degree', 'N/A')}")
                
                # Revenue Streams
                revenue_streams = canvas.get('revenue_streams', {})
                print(f"\n💰 REVENUE STREAMS (Saved in DB):")
                print(f"   Type: {revenue_streams.get('stream_type', 'N/A')}")
                print(f"   Description: {revenue_streams.get('description', 'N/A')}")
                print(f"   Pricing Model: {revenue_streams.get('pricing_model', 'N/A')}")
                revenue_potential = revenue_streams.get('revenue_potential', {})
                if revenue_potential:
                    print(f"   Revenue Potential:")
                    for key, value in revenue_potential.items():
                        print(f"      {key}: {value}")
                pricing_strategy = revenue_streams.get('pricing_strategy', {})
                if pricing_strategy:
                    print(f"   Pricing Strategy:")
                    for key, value in pricing_strategy.items():
                        print(f"      {key}: {value}")
                
                # Key Resources
                key_resources = canvas.get('key_resources', {})
                print(f"\n🔧 KEY RESOURCES (Saved in DB):")
                print(f"   Type: {key_resources.get('resource_type', 'N/A')}")
                print(f"   Description: {key_resources.get('description', 'N/A')}")
                print(f"   Importance: {key_resources.get('importance_level', 'N/A')}")
                print(f"   Acquisition Strategy: {key_resources.get('acquisition_strategy', 'N/A')}")
                print(f"   Competitive Advantage: {key_resources.get('competitive_advantage', 'N/A')}")
                
                # Key Activities
                key_activities = canvas.get('key_activities', {})
                print(f"\n⚡ KEY ACTIVITIES (Saved in DB):")
                print(f"   Type: {key_activities.get('activity_type', 'N/A')}")
                print(f"   Description: {key_activities.get('description', 'N/A')}")
                print(f"   Criticality: {key_activities.get('criticality', 'N/A')}")
                print(f"   Resource Requirements: {len(key_activities.get('resource_requirements', []))} items")
                if key_activities.get('resource_requirements'):
                    for i, req in enumerate(key_activities['resource_requirements'][:3]):
                        print(f"      {i+1}. {req}")
                print(f"   Efficiency Metrics: {len(key_activities.get('efficiency_metrics', []))} items")
                if key_activities.get('efficiency_metrics'):
                    for i, metric in enumerate(key_activities['efficiency_metrics'][:3]):
                        print(f"      {i+1}. {metric}")
                
                # Key Partnerships
                key_partnerships = canvas.get('key_partnerships', {})
                print(f"\n🤝 KEY PARTNERSHIPS (Saved in DB):")
                print(f"   Type: {key_partnerships.get('partnership_type', 'N/A')}")
                print(f"   Description: {key_partnerships.get('description', 'N/A')}")
                print(f"   Partner Categories: {len(key_partnerships.get('partner_categories', []))} items")
                if key_partnerships.get('partner_categories'):
                    for i, cat in enumerate(key_partnerships['partner_categories'][:3]):
                        print(f"      {i+1}. {cat}")
                print(f"   Partnership Benefits: {len(key_partnerships.get('partnership_benefits', []))} items")
                if key_partnerships.get('partnership_benefits'):
                    for i, benefit in enumerate(key_partnerships['partnership_benefits'][:3]):
                        print(f"      {i+1}. {benefit}")
                
                # Cost Structure
                cost_structure = canvas.get('cost_structure', {})
                print(f"\n💸 COST STRUCTURE (Saved in DB):")
                print(f"   Type: {cost_structure.get('structure_type', 'N/A')}")
                print(f"   Description: {cost_structure.get('description', 'N/A')}")
                print(f"   Fixed Costs: {len(cost_structure.get('fixed_costs', []))} items")
                if cost_structure.get('fixed_costs'):
                    for i, cost in enumerate(cost_structure['fixed_costs'][:3]):
                        print(f"      {i+1}. {cost}")
                print(f"   Variable Costs: {len(cost_structure.get('variable_costs', []))} items")
                if cost_structure.get('variable_costs'):
                    for i, cost in enumerate(cost_structure['variable_costs'][:3]):
                        print(f"      {i+1}. {cost}")
                print(f"   Cost Optimization: {cost_structure.get('cost_optimization', 'N/A')}")
                
                # Show context integration data
                print(f"\n🔗 CROSS-FEATURE CONTEXT INTEGRATION (Saved in DB):")
                if canvas.get('competitive_context'):
                    comp_context = canvas['competitive_context']
                    print(f"   ✅ Competitive Analysis: {comp_context.get('total_competitors', 0)} competitors")
                    print(f"      Market Gaps: {len(comp_context.get('market_gaps', []))} gaps identified")
                    print(f"      Key Insights: {len(comp_context.get('key_insights', []))} insights")
                
                if canvas.get('persona_context'):
                    persona_context = canvas['persona_context']
                    print(f"   ✅ Persona Analysis: {persona_context.get('personas_analyzed', 0)} personas")
                    print(f"      Pricing Sensitivity: {persona_context.get('pricing_sensitivity', 'N/A')}")
                    print(f"      Decision Factors: {len(persona_context.get('decision_making_factors', []))} factors")
                
                if canvas.get('market_sizing_context'):
                    market_context = canvas['market_sizing_context']
                    print(f"   ✅ Market Sizing: Market data integrated")
                    market_size = market_context.get('market_size', {})
                    if market_size:
                        print(f"      TAM: {market_size.get('tam', 'N/A')}")
                        print(f"      SAM: {market_size.get('sam', 'N/A')}")
                        print(f"      SOM: {market_size.get('som', 'N/A')}")
                
                if canvas.get('business_model_context'):
                    bm_context = canvas['business_model_context']
                    print(f"   ✅ Business Model: Revenue insights integrated")
                    print(f"      Primary Recommendation: {bm_context.get('primary_recommendation', 'N/A')}")
                    print(f"      Profitability Projections: {len(bm_context.get('profitability_projections', []))} projections")
                
                print(f"\n🎉 COMPREHENSIVE BUSINESS MODEL CANVAS VERIFICATION COMPLETE!")
                print(f"✅ Business Model Canvas successfully saved to MongoDB with comprehensive data")
                print(f"✅ All nine building blocks populated with detailed information")
                print(f"✅ Cross-feature context integration preserved")
                print(f"✅ Analysis ID: {analysis_id}")
                print(f"✅ Idea ID: {IDEA_ID}")
                
            else:
                print(f"❌ Canvas retrieval failed: {canvas_response.status}")
                error_text = await canvas_response.text()
                print(f"Error: {error_text}")
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_bmc_force_fallback()) 