#!/usr/bin/env python3
"""
Simple test for market sizing API
"""

import asyncio
import aiohttp
import json
import time


async def test_market_sizing_simple():
    """Simple test for market sizing API"""
    
    base_url = "http://localhost:8000"
    
    # Wait a bit for server to start
    await asyncio.sleep(3)
    
    async with aiohttp.ClientSession() as session:
        try:
            print("🧪 Testing Market Sizing API Connection")
            print("=" * 50)
            
            # Test 1: Check if server is running
            print("\n1️⃣ Testing server connection...")
            try:
                async with session.get(f"{base_url}/docs", timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        print("✅ Server is running and accessible")
                    else:
                        print(f"⚠️ Server returned status {response.status}")
            except Exception as e:
                print(f"❌ Cannot connect to server: {e}")
                return
            
            # Test 2: Test market sizing options endpoint
            print("\n2️⃣ Testing market sizing options...")
            try:
                async with session.get(f"{base_url}/api/v1/market-sizing/options", timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        options = await response.json()
                        print("✅ Market sizing options endpoint working")
                        print(f"   Available regions: {len(options.get('geographic_scopes', {}).get('regions', {}))}")
                    else:
                        error = await response.text()
                        print(f"❌ Options endpoint failed: {response.status} - {error}")
            except Exception as e:
                print(f"❌ Options endpoint error: {e}")
            
            # Test 3: Simple unauthenticated market sizing analysis
            print("\n3️⃣ Testing simple market sizing analysis...")
            
            simple_request = {
                "business_idea": "Mobile app for food delivery",
                "industry": "Food Technology",
                "target_market": "Urban professionals who order food online",
                "geographic_scope": "usa",
                "customer_type": "b2c",
                "revenue_model": "marketplace",
                "estimated_price_point": 2.99
            }
            
            try:
                start_time = time.time()
                async with session.post(
                    f"{base_url}/api/v1/market-sizing/analyze", 
                    json=simple_request,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    
                    execution_time = time.time() - start_time
                    
                    if response.status == 200:
                        result = await response.json()
                        print("✅ Market sizing analysis completed!")
                        print(f"   Execution time: {execution_time:.2f} seconds")
                        print(f"   Status: {result.get('status')}")
                        
                        # Show basic results
                        if 'report' in result:
                            tam_sam_som = result['report'].get('tam_sam_som', {})
                            print(f"   TAM: ${tam_sam_som.get('tam', 0):,.0f}")
                            print(f"   SAM: ${tam_sam_som.get('sam', 0):,.0f}")
                            print(f"   SOM: ${tam_sam_som.get('som', 0):,.0f}")
                        
                    else:
                        error = await response.text()
                        print(f"❌ Market sizing failed: {response.status}")
                        print(f"   Error: {error}")
                        
            except asyncio.TimeoutError:
                print("❌ Market sizing analysis timed out")
            except Exception as e:
                print(f"❌ Market sizing analysis error: {e}")
            
            print("\n🎉 Market Sizing API Test Complete!")
            
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_market_sizing_simple()) 