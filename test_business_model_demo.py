#!/usr/bin/env python3
import asyncio
import aiohttp
import json

# Test configuration
BASE_URL = "http://localhost:8000/api/v1"

async def test_business_model_demo():
    """
    Demo of the business model feature
    """
    print("🚀 Business Model Feature Demo\n")
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. Test business model options (no auth required)
            print("1. ⚙️ Testing Business Model Options...")
            options_response = await session.get(f"{BASE_URL}/business-model/options")
            
            if options_response.status == 200:
                options_data = await options_response.json()
                print("✅ Business model options retrieved successfully!")
                print(f"   📊 Revenue Models: {len(options_data.get('revenue_models', []))} options")
                print(f"   💲 Pricing Strategies: {len(options_data.get('pricing_strategies', []))} options")
                print(f"   🏭 Industries: {len(options_data.get('industries', []))} options")
                print(f"   💰 Cost Categories: {len(options_data.get('cost_categories', []))} options")
                
                # Show some examples
                revenue_models = options_data.get('revenue_models', [])
                print(f"\n   📋 Sample Revenue Models:")
                for model in revenue_models[:3]:
                    print(f"      • {model['label']}")
                    
            else:
                print(f"❌ Options failed: {options_response.status}")
                return
            
            # 2. Test business model analysis (without auth - will use fallback)
            print("\n2. 💰 Testing Business Model Analysis (Demo Mode)...")
            business_model_request = {
                "business_idea": "We help e-commerce businesses solve inventory forecasting problems by providing an AI-powered demand prediction platform",
                "target_market": "e-commerce businesses",
                "industry": "e-commerce analytics software",
                "estimated_users": 500,
                "development_cost": 75000,
                "operational_cost_monthly": 8000
            }
            
            business_model_response = await session.post(
                f"{BASE_URL}/business-model/analyze",
                json=business_model_request
            )
            
            if business_model_response.status == 200:
                business_model_data = await business_model_response.json()
                report = business_model_data.get('report', {})
                
                print("✅ Business model analysis completed successfully!")
                print(f"   Analysis ID: {business_model_data.get('analysis_id', 'Demo Mode')}")
                
                # Show primary recommendation
                primary_rec = report.get('primary_recommendation', {})
                if primary_rec:
                    print(f"\n🎯 PRIMARY REVENUE MODEL RECOMMENDATION:")
                    print(f"   Model Type: {primary_rec.get('model_type', 'N/A')}")
                    print(f"   Recommended Price: ${primary_rec.get('recommended_price', 'N/A')}")
                    print(f"   Suitability Score: {primary_rec.get('suitability_score', 0):.1f}/10")
                    print(f"   Implementation: {primary_rec.get('implementation_complexity', 'N/A')}")
                    print(f"   Time to Revenue: {primary_rec.get('time_to_revenue', 'N/A')}")
                
                # Show all revenue model recommendations
                recommendations = report.get('recommended_revenue_models', [])
                if recommendations:
                    print(f"\n📊 ALL REVENUE MODEL RECOMMENDATIONS:")
                    for i, rec in enumerate(recommendations, 1):
                        print(f"   {i}. {rec.get('model_type', 'N/A')} (Score: {rec.get('suitability_score', 0):.1f}/10)")
                        print(f"      Price: ${rec.get('recommended_price', 'N/A')}")
                        print(f"      Pros: {', '.join(rec.get('pros', [])[:2])}")
                
                # Show profitability projections
                projections = report.get('profitability_projections', [])
                if projections:
                    print(f"\n💰 PROFITABILITY PROJECTIONS:")
                    scenario_names = ["Conservative", "Realistic", "Optimistic"]
                    for i, proj in enumerate(projections):
                        scenario = scenario_names[i] if i < len(scenario_names) else f"Scenario {i+1}"
                        print(f"   {scenario}:")
                        print(f"     Monthly Revenue: ${proj.get('monthly_revenue', 0):,.0f}")
                        print(f"     Annual Revenue: ${proj.get('annual_revenue', 0):,.0f}")
                        print(f"     Break-even: {proj.get('break_even_months', 0)} months")
                        print(f"     ROI: {proj.get('roi_percentage', 0):.1f}%")
                
                # Show pricing insights
                pricing = report.get('pricing_insights', {})
                if pricing:
                    print(f"\n💲 PRICING STRATEGY INSIGHTS:")
                    print(f"   Recommended Strategy: {pricing.get('recommended_strategy', 'N/A')}")
                    if pricing.get('suggested_pricing_tiers'):
                        print(f"   Pricing Tiers: {len(pricing['suggested_pricing_tiers'])} tiers suggested")
                
                # Show market benchmarks
                benchmarks = report.get('market_benchmarks', {})
                if benchmarks:
                    print(f"\n📈 MARKET BENCHMARKS:")
                    print(f"   Industry CAC: ${benchmarks.get('industry_cac', 0):.2f}")
                    print(f"   Industry LTV: ${benchmarks.get('industry_ltv', 0):.2f}")
                    print(f"   LTV:CAC Ratio: {benchmarks.get('ltv_cac_ratio', 0):.1f}")
                    print(f"   Market Growth Rate: {benchmarks.get('market_growth_rate', 0):.1%}")
                
                # Show implementation roadmap
                roadmap = report.get('implementation_roadmap', [])
                if roadmap:
                    print(f"\n🗺️ IMPLEMENTATION ROADMAP:")
                    for i, step in enumerate(roadmap[:5], 1):
                        print(f"   {i}. {step}")
                
                # Show risk factors
                risks = report.get('risk_factors', [])
                if risks:
                    print(f"\n⚠️ KEY RISK FACTORS:")
                    for i, risk in enumerate(risks[:3], 1):
                        print(f"   {i}. {risk}")
                
                # Show success metrics
                metrics = report.get('success_metrics', [])
                if metrics:
                    print(f"\n📊 SUCCESS METRICS TO TRACK:")
                    for i, metric in enumerate(metrics[:4], 1):
                        print(f"   {i}. {metric}")
                
                print(f"\n🎉 BUSINESS MODEL FEATURE DEMO SUCCESSFUL!")
                print(f"✅ Comprehensive revenue model recommendations generated")
                print(f"✅ Multi-scenario profitability projections calculated")
                print(f"✅ Intelligent pricing strategy insights provided")
                print(f"✅ Industry market benchmarks included")
                print(f"✅ Actionable implementation roadmap created")
                print(f"✅ Risk factors and success metrics identified")
                
            else:
                print(f"❌ Business model analysis failed: {business_model_response.status}")
                error_text = await business_model_response.text()
                print(f"Error: {error_text}")
            
            # 3. Show API documentation link
            print(f"\n📚 API Documentation:")
            print(f"   Full API docs: http://localhost:8000/docs")
            print(f"   Business Model endpoints: http://localhost:8000/docs#/Business%20Model%20Analysis")
            
        except Exception as e:
            print(f"❌ Demo failed with error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_business_model_demo()) 