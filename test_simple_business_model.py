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

async def test_simple_business_model():
    """
    Simple test of the business model feature
    """
    print("🚀 Testing Business Model Feature\n")
    
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
            
            # 4. Test business model analysis directly
            print("\n4. 💰 Testing Business Model Analysis...")
            business_model_request = {
                "business_idea": questionnaire_data["questionnaire"]["business_idea_description"],
                "target_market": "e-commerce businesses",
                "industry": "e-commerce analytics software",
                "estimated_users": 500,
                "development_cost": 75000,
                "operational_cost_monthly": 8000,
                "idea_id": idea_id
            }
            
            business_model_response = await session.post(
                f"{BASE_URL}/business-model/analyze",
                headers=headers,
                json=business_model_request
            )
            
            if business_model_response.status == 200:
                business_model_data = await business_model_response.json()
                report = business_model_data.get('report', {})
                
                print("✅ Business model analysis completed successfully!")
                print(f"   Analysis ID: {business_model_data.get('analysis_id')}")
                
                # Show primary recommendation
                primary_rec = report.get('primary_recommendation', {})
                if primary_rec:
                    print(f"\n🎯 PRIMARY REVENUE MODEL:")
                    print(f"   Model Type: {primary_rec.get('model_type', 'N/A')}")
                    print(f"   Recommended Price: ${primary_rec.get('recommended_price', 'N/A')}")
                    print(f"   Suitability Score: {primary_rec.get('suitability_score', 0):.1f}/10")
                    print(f"   Implementation: {primary_rec.get('implementation_complexity', 'N/A')}")
                
                # Show profitability projections
                projections = report.get('profitability_projections', [])
                if projections:
                    print(f"\n💰 PROFITABILITY PROJECTIONS:")
                    for i, proj in enumerate(projections[:2]):  # Show first 2 scenarios
                        scenario = "Conservative" if i == 0 else "Realistic"
                        print(f"   {scenario}:")
                        print(f"     Monthly Revenue: ${proj.get('monthly_revenue', 0):,.0f}")
                        print(f"     Break-even: {proj.get('break_even_months', 0)} months")
                        print(f"     ROI: {proj.get('roi_percentage', 0):.1f}%")
                
                # Show pricing insights
                pricing = report.get('pricing_insights', {})
                if pricing:
                    print(f"\n💲 PRICING STRATEGY:")
                    print(f"   Strategy: {pricing.get('recommended_strategy', 'N/A')}")
                
                # Show market benchmarks
                benchmarks = report.get('market_benchmarks', {})
                if benchmarks:
                    print(f"\n📈 MARKET BENCHMARKS:")
                    print(f"   Industry CAC: ${benchmarks.get('industry_cac', 0):.2f}")
                    print(f"   Industry LTV: ${benchmarks.get('industry_ltv', 0):.2f}")
                    print(f"   LTV:CAC Ratio: {benchmarks.get('ltv_cac_ratio', 0):.1f}")
                
                # Show implementation roadmap
                roadmap = report.get('implementation_roadmap', [])
                if roadmap:
                    print(f"\n🗺️ IMPLEMENTATION ROADMAP:")
                    for i, step in enumerate(roadmap[:3], 1):
                        print(f"   {i}. {step}")
                
                print(f"\n🎉 BUSINESS MODEL FEATURE TEST SUCCESSFUL!")
                print(f"✅ Revenue model recommendations generated")
                print(f"✅ Profitability projections calculated")
                print(f"✅ Pricing strategy insights provided")
                print(f"✅ Market benchmarks included")
                print(f"✅ Implementation roadmap created")
                
            else:
                print(f"❌ Business model analysis failed: {business_model_response.status}")
                error_text = await business_model_response.text()
                print(f"Error: {error_text}")
            
            # 5. Test business model options endpoint
            print("\n5. ⚙️ Testing Business Model Options...")
            options_response = await session.get(f"{BASE_URL}/business-model/options")
            
            if options_response.status == 200:
                options_data = await options_response.json()
                print("✅ Business model options retrieved:")
                print(f"   Revenue models: {len(options_data.get('revenue_models', []))}")
                print(f"   Pricing strategies: {len(options_data.get('pricing_strategies', []))}")
                print(f"   Industries: {len(options_data.get('industries', []))}")
            else:
                print(f"❌ Options failed: {options_response.status}")
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simple_business_model()) 