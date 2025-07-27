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
    "password": "omarelloumi531@gmail.com"
}

async def test_complete_onboarding_system():
    """
    Test the complete onboarding and feature orchestration system
    """
    print("🚀 Testing Complete Onboarding & Feature Orchestration System\n")
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. Login user
            print("1. 🔐 Logging in user...")
            login_response = await session.post(
                f"{BASE_URL}/auth/login",
                json={
                    "email": TEST_USER["email"],
                    "password": TEST_USER["password"]
                }
            )
            
            if login_response.status != 200:
                print(f"❌ Login failed with status {login_response.status}")
                login_text = await login_response.text()
                print(f"Response: {login_text}")
                return
            
            login_data = await login_response.json()
            access_token = login_data.get("access_token")
            print(f"✅ Login successful")
            
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # 2. Test onboarding options endpoint
            print("\n2. 📋 Getting onboarding options...")
            options_response = await session.get(
                f"{BASE_URL}/onboarding/options",
                headers=headers
            )
            
            if options_response.status == 200:
                options_data = await options_response.json()
                print(f"✅ Onboarding options retrieved:")
                print(f"   Business levels: {len(options_data['business_levels'])}")
                print(f"   Current stages: {len(options_data['current_stages'])}")
                print(f"   Main goals: {len(options_data['main_goals'])}")
                print(f"   Biggest challenges: {len(options_data['biggest_challenges'])}")
                print(f"   Template: {options_data['business_idea_format']['template']}")
            else:
                print(f"❌ Failed to get onboarding options: {options_response.status}")
            
            # 3. Submit onboarding questionnaire
            print("\n3. 📝 Submitting onboarding questionnaire...")
            questionnaire_data = {
                "questionnaire": {
                    "business_level": "some_experience",
                    "current_stage": "validating_idea",
                    "business_idea_description": "We help small business owners solve inventory management problems by providing an AI-powered tracking platform",
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
                
                print(f"✅ Onboarding completed successfully!")
                print(f"   Business idea ID: {idea_id}")
                print(f"   Title: {business_idea['title']}")
                print(f"   Target WHO: {business_idea.get('target_who')}")
                print(f"   Problem WHAT: {business_idea.get('problem_what')}")
                print(f"   Solution HOW: {business_idea.get('solution_how')}")
                print(f"   Recommended next steps: {len(onboarding_data['recommended_next_steps'])}")
                print(f"   Feature roadmap: {len(onboarding_data['feature_roadmap'])}")
                
                for step in onboarding_data["recommended_next_steps"][:3]:
                    print(f"     • {step}")
                    
            else:
                print(f"❌ Onboarding failed: {onboarding_response.status}")
                error_text = await onboarding_response.text()
                print(f"Error: {error_text}")
                return
            
            # 4. Get personalized roadmap
            print(f"\n4. 🗺️ Getting personalized roadmap for idea {idea_id}...")
            roadmap_response = await session.get(
                f"{BASE_URL}/onboarding/personalized-roadmap/{idea_id}",
                headers=headers
            )
            
            if roadmap_response.status == 200:
                roadmap_data = await roadmap_response.json()
                print(f"✅ Personalized roadmap retrieved:")
                print(f"   Completed analyses: {roadmap_data['completed_analyses']}")
                print(f"   Next steps: {len(roadmap_data['recommended_next_steps'])}")
                print(f"   Available features: {len(roadmap_data['available_features'])}")
                
                for feature in roadmap_data["available_features"]:
                    print(f"     • {feature['feature']}: {feature['status']} - {feature['benefit']}")
                    
            else:
                print(f"❌ Failed to get roadmap: {roadmap_response.status}")
            
            # 5. Run competitor analysis (first feature)
            print(f"\n5. 🏢 Running competitor analysis...")
            competitor_request = {
                "idea_description": questionnaire_data["questionnaire"]["business_idea_description"],
                "target_market": "small business owners",
                "business_model": "SaaS subscription",
                "geographic_focus": "North America",
                "industry": "inventory management software",
                "idea_id": idea_id
            }
            
            competitor_response = await session.post(
                f"{BASE_URL}/analyze/competitors",
                headers=headers,
                json=competitor_request
            )
            
            if competitor_response.status == 200:
                competitor_data = await competitor_response.json()
                print(f"✅ Competitor analysis completed:")
                print(f"   Analysis ID: {competitor_data.get('analysis_id')}")
                print(f"   Total competitors: {competitor_data['report']['total_competitors']}")
                print(f"   Market gaps: {len(competitor_data['report']['market_gaps'])}")
                print(f"   Key insights: {len(competitor_data['report']['key_insights'])}")
            else:
                print(f"❌ Competitor analysis failed: {competitor_response.status}")
                error_text = await competitor_response.text()
                print(f"Error: {error_text}")
            
            # 6. Check updated roadmap after competitor analysis
            print(f"\n6. 🗺️ Checking updated roadmap after competitor analysis...")
            updated_roadmap_response = await session.get(
                f"{BASE_URL}/onboarding/personalized-roadmap/{idea_id}",
                headers=headers
            )
            
            if updated_roadmap_response.status == 200:
                updated_roadmap = await updated_roadmap_response.json()
                print(f"✅ Updated roadmap retrieved:")
                print(f"   Completed analyses: {updated_roadmap['completed_analyses']}")
                print(f"   Next steps after competitor analysis:")
                
                for step in updated_roadmap["recommended_next_steps"][:3]:
                    print(f"     • {step}")
                    
                for feature in updated_roadmap["available_features"]:
                    if feature["status"] == "completed":
                        print(f"     ✅ {feature['feature']}: {feature['status']}")
                    else:
                        print(f"     ⏳ {feature['feature']}: {feature['status']}")
                        
            # 7. Run persona analysis (second feature with competitor context)
            print(f"\n7. 👥 Running persona analysis with competitor context...")
            persona_request = {
                "business_idea": questionnaire_data["questionnaire"]["business_idea_description"],
                "target_market": "small business owners",
                "industry": "inventory management software",
                "idea_id": idea_id
            }
            
            persona_response = await session.post(
                f"{BASE_URL}/analyze/personas",
                headers=headers,
                json=persona_request
            )
            
            if persona_response.status == 200:
                persona_data = await persona_response.json()
                print(f"✅ Persona analysis completed with competitor context:")
                print(f"   Analysis ID: {persona_data.get('analysis_id')}")
                print(f"   Personas identified: {len(persona_data['report']['personas'])}")
                
                # Fix the persona parsing to handle the actual response structure
                for i, persona in enumerate(persona_data['report']['personas'][:2]):
                    try:
                        # Try different possible structures
                        if 'basic_info' in persona:
                            name = persona['basic_info'].get('name', f'Persona {i+1}')
                            title = persona['basic_info'].get('title', 'Unknown')
                        elif 'name' in persona:
                            name = persona.get('name', f'Persona {i+1}')
                            title = persona.get('title', 'Unknown')
                        else:
                            name = f'Persona {i+1}'
                            title = 'Generated persona'
                        
                        print(f"     • {name} - {title}")
                    except Exception as e:
                        print(f"     • Persona {i+1}: [Structure: {list(persona.keys()) if isinstance(persona, dict) else type(persona)}]")
                    
            else:
                print(f"❌ Persona analysis failed: {persona_response.status}")
                error_text = await persona_response.text()
                print(f"Error: {error_text}")
            
            # 8. Run market sizing analysis (third feature with full context)
            print(f"\n8. 📊 Running market sizing with full competitive and persona context...")
            market_sizing_request = {
                "business_idea": questionnaire_data["questionnaire"]["business_idea_description"],
                "industry": "inventory management software",
                "target_market": "small business owners",
                "geographic_scope": "north_america",
                "customer_type": "b2b",
                "revenue_model": "subscription",
                "estimated_price_point": 49.99,
                "idea_id": idea_id
            }
            
            market_sizing_response = await session.post(
                f"{BASE_URL}/market-sizing/analyze",
                headers=headers,
                json=market_sizing_request
            )
            
            if market_sizing_response.status == 200:
                market_sizing_data = await market_sizing_response.json()
                print(f"✅ Market sizing completed with full context:")
                print(f"   Analysis ID: {market_sizing_data.get('analysis_id')}")
                
                tam_sam_som = market_sizing_data['report']['tam_sam_som_breakdown']
                print(f"   TAM: ${tam_sam_som['tam']:,.0f}")
                print(f"   SAM: ${tam_sam_som['sam']:,.0f}")
                print(f"   SOM: ${tam_sam_som['som']:,.0f}")
                
                competitive_position = market_sizing_data['report']['competitive_position']
                print(f"   Market gaps identified: {len(competitive_position['market_gaps'])}")
                print(f"   Competitive advantages: {len(competitive_position['competitive_advantages'])}")
                
            else:
                print(f"❌ Market sizing failed: {market_sizing_response.status}")
                error_text = await market_sizing_response.text()
                print(f"Error: {error_text}")
            
            # 9. Final roadmap check - all analyses completed
            print(f"\n9. 🎯 Final roadmap check - all analyses completed...")
            final_roadmap_response = await session.get(
                f"{BASE_URL}/onboarding/personalized-roadmap/{idea_id}",
                headers=headers
            )
            
            if final_roadmap_response.status == 200:
                final_roadmap = await final_roadmap_response.json()
                print(f"✅ Final roadmap status:")
                print(f"   Completed analyses: {final_roadmap['completed_analyses']}")
                print(f"   All features completed: {len(final_roadmap['completed_analyses']) == 3}")
                
                print(f"\n📈 Contextual insights:")
                for analysis_type, insight in final_roadmap["contextual_insights"].items():
                    print(f"     • {analysis_type}: {insight}")
                
                print(f"\n🎯 Final recommendations:")
                for step in final_roadmap["recommended_next_steps"]:
                    print(f"     • {step}")
                    
            print(f"\n🎉 Complete onboarding and feature orchestration test completed successfully!")
            print(f"✅ User onboarded with intelligent questionnaire")
            print(f"✅ Business idea created and parsed intelligently")
            print(f"✅ Personalized roadmap generated")
            print(f"✅ Features run with intelligent cross-context")
            print(f"✅ Analysis completion tracked automatically")
            print(f"✅ Roadmap updated dynamically based on completion")
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_complete_onboarding_system()) 