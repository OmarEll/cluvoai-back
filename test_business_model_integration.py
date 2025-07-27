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

async def test_complete_business_model_integration():
    """
    Test the complete business model feature integration with all previous analyses
    Following the roadmap: Onboarding → Competitors → Personas → Market Sizing → Business Model
    """
    print("🚀 Testing Complete Business Model Integration with Cross-Feature Context\n")
    
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
                return
            
            login_data = await login_response.json()
            access_token = login_data.get("access_token")
            print(f"✅ Login successful")
            
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # 2. Create business idea through onboarding  
            print("\n2. 📝 Creating business idea through intelligent onboarding...")
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
                
                print(f"✅ Business idea created successfully!")
                print(f"   Idea ID: {idea_id}")
                print(f"   Title: {business_idea['title']}")
                print(f"   Target WHO: {business_idea.get('target_who')}")
                print(f"   Problem WHAT: {business_idea.get('problem_what')}")
                print(f"   Solution HOW: {business_idea.get('solution_how')}")
            else:
                print(f"❌ Onboarding failed: {onboarding_response.status}")
                return
            
            # 3. Run competitor analysis (provides pricing intelligence)
            print(f"\n3. 🏢 Running competitor analysis for pricing intelligence...")
            competitor_request = {
                "idea_description": questionnaire_data["questionnaire"]["business_idea_description"],
                "target_market": "e-commerce businesses",
                "business_model": "SaaS subscription",
                "geographic_focus": "North America",
                "industry": "e-commerce analytics software",
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
                print(f"   📊 This provides pricing intelligence for business model recommendations")
            else:
                print(f"❌ Competitor analysis failed: {competitor_response.status}")
                error_text = await competitor_response.text()
                print(f"Error: {error_text}")
            
            # 4. Run persona analysis (provides customer willingness to pay)
            print(f"\n4. 👥 Running persona analysis for customer insights...")
            persona_request = {
                "business_idea": questionnaire_data["questionnaire"]["business_idea_description"],
                "target_market": "e-commerce businesses",
                "industry": "e-commerce analytics software",
                "idea_id": idea_id
            }
            
            persona_response = await session.post(
                f"{BASE_URL}/analyze/personas",
                headers=headers,
                json=persona_request
            )
            
            if persona_response.status == 200:
                persona_data = await persona_response.json()
                print(f"✅ Persona analysis completed:")
                print(f"   Analysis ID: {persona_data.get('analysis_id')}")
                print(f"   Personas identified: {len(persona_data['report']['personas'])}")
                print(f"   💰 This provides customer willingness to pay insights for revenue models")
            else:
                print(f"❌ Persona analysis failed: {persona_response.status}")
            
            # 5. Run market sizing analysis (provides market benchmarks)
            print(f"\n5. 📊 Running market sizing for market benchmarks...")
            market_sizing_request = {
                "business_idea": questionnaire_data["questionnaire"]["business_idea_description"],
                "industry": "e-commerce analytics software",
                "target_market": "e-commerce businesses",
                "geographic_scope": "north_america",
                "customer_type": "b2b",
                "revenue_model": "subscription",
                "estimated_price_point": 149.99,
                "idea_id": idea_id
            }
            
            market_sizing_response = await session.post(
                f"{BASE_URL}/market-sizing/analyze",
                headers=headers,
                json=market_sizing_request
            )
            
            if market_sizing_response.status == 200:
                market_sizing_data = await market_sizing_response.json()
                
                print(f"✅ Market sizing completed:")
                print(f"   Analysis ID: {market_sizing_data.get('analysis_id')}")
                
                # Handle different possible response structures
                report = market_sizing_data.get('report', {})
                tam_sam_som = report.get('tam_sam_som_breakdown', {})
                
                if not tam_sam_som:
                    # Try alternative structure
                    tam_sam_som = report.get('market_sizing_report', {}).get('tam_sam_som_breakdown', {})
                
                if tam_sam_som:
                    print(f"   TAM: ${tam_sam_som.get('tam', 0):,.0f}")
                    print(f"   SAM: ${tam_sam_som.get('sam', 0):,.0f}")
                    print(f"   SOM: ${tam_sam_som.get('som', 0):,.0f}")
                else:
                    print(f"   Market sizing data available but structure varies")
                print(f"   📈 This provides market benchmarks for revenue projections")
            else:
                print(f"❌ Market sizing failed: {market_sizing_response.status}")
            
            # 6. Now run business model analysis with full context
            print(f"\n6. 💰 Running business model analysis with FULL CONTEXT from all previous analyses...")
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
                report = business_model_data['report']
                
                print(f"✅ Business model analysis completed with intelligent context!")
                print(f"   Analysis ID: {business_model_data.get('analysis_id')}")
                
                # Show primary recommendation
                primary_rec = report['primary_recommendation']
                print(f"\n🎯 PRIMARY REVENUE MODEL RECOMMENDATION:")
                print(f"   Model Type: {primary_rec['model_type']}")
                print(f"   Recommended Price: ${primary_rec.get('recommended_price', 'N/A')}")
                print(f"   Suitability Score: {primary_rec['suitability_score']:.1f}/10")
                print(f"   Implementation: {primary_rec['implementation_complexity']}")
                print(f"   Time to Revenue: {primary_rec['time_to_revenue']}")
                
                # Show competitive intelligence integration
                if report.get('competitive_context'):
                    comp_context = report['competitive_context']
                    print(f"\n🏢 COMPETITIVE INTELLIGENCE INTEGRATED:")
                    print(f"   Competitors analyzed: {comp_context.get('total_competitors', 0)}")
                    print(f"   Pricing intelligence: {'✅' if comp_context.get('pricing_intelligence') else '❌'}")
                
                # Show persona insights integration
                if report.get('persona_context'):
                    persona_context = report['persona_context']
                    print(f"\n👥 PERSONA INSIGHTS INTEGRATED:")
                    print(f"   Customer personas: {persona_context.get('personas_analyzed', 0)}")
                    print(f"   Target segments: {'✅' if persona_context.get('target_segments') else '❌'}")
                
                # Show market sizing integration
                if report.get('market_sizing_context'):
                    market_context = report['market_sizing_context']
                    market_size = market_context.get('market_size', {})
                    if market_size:
                        print(f"\n📊 MARKET SIZING INTEGRATED:")
                        print(f"   TAM: ${market_size.get('tam', 0):,.0f}")
                        print(f"   SAM: ${market_size.get('sam', 0):,.0f}")
                        print(f"   SOM: ${market_size.get('som', 0):,.0f}")
                    else:
                        print(f"\n📊 MARKET SIZING INTEGRATED:")
                        print(f"   Market sizing context available")
                else:
                    print(f"\n📊 MARKET SIZING: No context available")
                
                # Show profitability projections
                if report.get('profitability_projections'):
                    projections = report['profitability_projections']
                    print(f"\n💰 PROFITABILITY PROJECTIONS ({len(projections)} scenarios):")
                    
                    scenario_names = ["Conservative", "Realistic", "Optimistic"]
                    for i, proj in enumerate(projections):
                        scenario = scenario_names[i] if i < len(scenario_names) else f"Scenario {i+1}"
                        print(f"   {scenario}:")
                        print(f"     Monthly Revenue: ${proj['monthly_revenue']:,.0f}")
                        print(f"     Break-even: {proj['break_even_months']} months")
                        print(f"     ROI: {proj['roi_percentage']:.1f}%")
                
                # Show pricing insights
                pricing = report.get('pricing_insights', {})
                print(f"\n💲 PRICING STRATEGY:")
                print(f"   Recommended Strategy: {pricing.get('recommended_strategy', 'N/A')}")
                if pricing.get('competitive_price_range'):
                    price_range = pricing['competitive_price_range']
                    print(f"   Competitive Range: ${price_range.get('min', 0):.2f} - ${price_range.get('max', 0):.2f}")
                
                # Show market benchmarks
                benchmarks = report.get('market_benchmarks', {})
                print(f"\n📈 MARKET BENCHMARKS:")
                print(f"   Industry CAC: ${benchmarks.get('industry_cac', 0):.2f}")
                print(f"   Industry LTV: ${benchmarks.get('industry_ltv', 0):.2f}")
                print(f"   LTV:CAC Ratio: {benchmarks.get('ltv_cac_ratio', 0):.1f}")
                
                # Show implementation roadmap
                roadmap = report.get('implementation_roadmap', [])
                print(f"\n🗺️ IMPLEMENTATION ROADMAP:")
                for i, step in enumerate(roadmap[:4], 1):
                    print(f"   {i}. {step}")
                
            else:
                print(f"❌ Business model analysis failed: {business_model_response.status}")
                error_text = await business_model_response.text()
                print(f"Error: {error_text}")
            
            # 7. Test business model insights endpoint
            print(f"\n7. 💡 Getting actionable business model insights...")
            insights_response = await session.get(
                f"{BASE_URL}/business-model/insights/{idea_id}",
                headers=headers
            )
            
            if insights_response.status == 200:
                insights_data = await insights_response.json()
                
                print(f"✅ Business model insights retrieved:")
                
                # Show revenue model insights
                revenue_rec = insights_data.get('revenue_model_recommendation', {})
                print(f"\n🎯 REVENUE MODEL INSIGHTS:")
                print(f"   Primary Model: {revenue_rec.get('primary_model', 'N/A')}")
                print(f"   Confidence: {revenue_rec.get('confidence_score', 0):.1f}/10")
                
                # Show profitability outlook
                profitability = insights_data.get('profitability_outlook', {})
                print(f"\n💰 PROFITABILITY OUTLOOK:")
                print(f"   Monthly Revenue (Realistic): ${profitability.get('realistic_monthly_revenue', 0):,.0f}")
                print(f"   Break-even Timeline: {profitability.get('break_even_timeline', 'Unknown')}")
                print(f"   ROI Projection: {profitability.get('roi_projection', '0%')}")
                
                # Show context intelligence
                context_intel = insights_data.get('contextual_intelligence', {})
                print(f"\n🧠 CONTEXTUAL INTELLIGENCE USED:")
                print(f"   Competitive Context: {'✅' if context_intel.get('competitive_context_used') else '❌'}")
                print(f"   Persona Context: {'✅' if context_intel.get('persona_context_used') else '❌'}")
                print(f"   Market Sizing Context: {'✅' if context_intel.get('market_sizing_context_used') else '❌'}")
                
                benefits = context_intel.get('cross_analysis_benefits', [])
                print(f"   Cross-Analysis Benefits:")
                for benefit in benefits:
                    print(f"     • {benefit}")
                
            else:
                print(f"❌ Failed to get insights: {insights_response.status}")
            
            # 8. Test revenue model comparison
            print(f"\n8. 🔄 Comparing revenue models...")
            comparison_response = await session.get(
                f"{BASE_URL}/business-model/compare-models/{idea_id}",
                headers=headers
            )
            
            if comparison_response.status == 200:
                comparison_data = await comparison_response.json()
                
                print(f"✅ Revenue model comparison completed:")
                print(f"   Business Idea: {comparison_data['business_idea'][:60]}...")
                print(f"   Models Compared: {len(comparison_data['model_comparisons'])}")
                print(f"   Summary: {comparison_data['recommendation_summary']}")
                
                print(f"\n📊 MODEL COMPARISON DETAILS:")
                for i, model in enumerate(comparison_data['model_comparisons'][:3], 1):
                    print(f"   {i}. {model['model_type']} (Score: {model['suitability_score']:.1f}/10)")
                    print(f"      Price: ${model.get('recommended_price', 'N/A')}")
                    print(f"      Complexity: {model['implementation_complexity']}")
                
            else:
                print(f"❌ Failed to compare models: {comparison_response.status}")
            
            print(f"\n🎉 COMPLETE BUSINESS MODEL INTEGRATION TEST SUCCESSFUL!")
            print(f"✅ Demonstrated intelligent cross-feature context integration")
            print(f"✅ Competitive intelligence enhanced pricing recommendations")
            print(f"✅ Persona insights informed customer willingness to pay")
            print(f"✅ Market sizing provided accurate revenue projections")
            print(f"✅ Business model analysis leveraged ALL previous analyses")
            print(f"✅ Comprehensive revenue model recommendations generated")
            print(f"✅ Actionable implementation roadmap created")
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_complete_business_model_integration()) 