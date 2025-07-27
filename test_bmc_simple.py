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

async def test_bmc_simple():
    """
    Simple test to check if BMC route is working
    """
    print(f"🎨 Simple Business Model Canvas Test\n")
    
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
            
            # 2. Test BMC generation
            print(f"\n2. 🎨 Testing BMC generation...")
            canvas_request = {
                "business_idea": "AI-powered demand prediction platform for e-commerce businesses",
                "target_market": "e-commerce businesses",
                "industry": "e-commerce analytics software"
            }
            
            print(f"   Request payload: {json.dumps(canvas_request, indent=2)}")
            
            generate_response = await session.post(
                f"{BASE_URL}/business-model-canvas/analyze",
                headers=headers,
                json=canvas_request
            )
            
            print(f"   Response status: {generate_response.status}")
            
            if generate_response.status == 200:
                generate_data = await generate_response.json()
                print(f"   ✅ BMC generation successful!")
                print(f"   Response keys: {list(generate_data.keys())}")
                print(f"   Analysis ID: {generate_data.get('analysis_id')}")
                print(f"   Idea ID: {generate_data.get('idea_id')}")
                print(f"   Message: {generate_data.get('message')}")
                
                # Check if canvas exists
                canvas = generate_data.get('canvas', {})
                if canvas:
                    print(f"   Canvas business idea: {canvas.get('business_idea')}")
                    print(f"   Canvas version: {canvas.get('version')}")
                    print(f"   Canvas status: {canvas.get('status')}")
                else:
                    print(f"   ❌ No canvas in response")
                
            else:
                print(f"   ❌ BMC generation failed")
                error_text = await generate_response.text()
                print(f"   Error: {error_text}")
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_bmc_simple()) 