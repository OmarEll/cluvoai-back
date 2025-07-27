#!/usr/bin/env python3
"""
Focused test script to debug feedback history issue
"""

import asyncio
import aiohttp
import json
from datetime import datetime


async def test_feedback_history_debug():
    """Debug the feedback history endpoint specifically"""
    
    base_url = "http://localhost:8000"
    
    # Test user credentials
    user_credentials = {
        "email": "feedback.tester@example.com",
        "password": "feedbacktest123"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            print("🔍 Debugging Feedback History Issue")
            print("=" * 50)
            
            # Step 1: Login
            print("\n1️⃣ Logging in...")
            async with session.post(
                f"{base_url}/api/v1/auth/login",
                json=user_credentials,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 200:
                    token_data = await response.json()
                    access_token = token_data['access_token']
                    print("✅ Login successful!")
                else:
                    print(f"❌ Login failed: {response.status}")
                    return False
            
            # Set headers for authenticated requests
            auth_headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Step 2: Test feedback history with detailed logging
            print("\n2️⃣ Testing feedback history with detailed logging...")
            print(f"Request URL: {base_url}/api/v1/feedback/my-history")
            print(f"Headers: {auth_headers}")
            
            async with session.get(
                f"{base_url}/api/v1/feedback/my-history",
                headers=auth_headers
            ) as response:
                
                print(f"Response Status: {response.status}")
                print(f"Response Headers: {dict(response.headers)}")
                
                if response.status == 200:
                    # Get raw response text first
                    raw_text = await response.text()
                    print(f"Raw Response Text: {raw_text}")
                    print(f"Raw Response Length: {len(raw_text)}")
                    
                    # Try to parse as JSON
                    try:
                        history = json.loads(raw_text)
                        print(f"Parsed JSON Type: {type(history)}")
                        print(f"Parsed JSON: {history}")
                        
                        if history is None:
                            print("❌ Response is None!")
                        elif isinstance(history, dict):
                            print("✅ Response is a dictionary")
                            print(f"Keys: {list(history.keys())}")
                            
                            total_count = history.get('total_count')
                            feedback_list = history.get('feedback_list')
                            
                            print(f"total_count: {total_count} (type: {type(total_count)})")
                            print(f"feedback_list: {feedback_list} (type: {type(feedback_list)})")
                            
                            if feedback_list is not None:
                                print(f"feedback_list length: {len(feedback_list)}")
                                for i, feedback in enumerate(feedback_list):
                                    print(f"  Feedback {i}: {feedback} (type: {type(feedback)})")
                            
                        else:
                            print(f"❌ Unexpected response type: {type(history)}")
                            
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON decode error: {e}")
                        
                else:
                    print(f"❌ Request failed with status: {response.status}")
                    error_text = await response.text()
                    print(f"Error response: {error_text}")
            
            # Step 3: Check if user has any feedback at all
            print("\n3️⃣ Checking if user has any feedback in the system...")
            
            # First let's check what analyses the user has
            async with session.get(
                f"{base_url}/api/v1/users/ideas",
                headers=auth_headers
            ) as response:
                
                if response.status == 200:
                    ideas = await response.json()
                    print(f"User has {len(ideas)} ideas")
                    
                    for idea in ideas:
                        print(f"  Idea: {idea.get('title', 'No title')} (ID: {idea.get('id', 'No ID')})")
                        
                        # Check analysis history for this idea
                        idea_id = idea.get('id')
                        if idea_id:
                            async with session.get(
                                f"{base_url}/api/v1/users/ideas/{idea_id}/analyses",
                                headers=auth_headers
                            ) as analyses_response:
                                
                                if analyses_response.status == 200:
                                    analyses_data = await analyses_response.json()
                                    analyses_list = analyses_data.get('analyses', [])
                                    print(f"    Analyses for this idea: {len(analyses_list)}")
                                    
                                    for analysis in analyses_list:
                                        analysis_id = analysis.get('id')
                                        analysis_type = analysis.get('analysis_type')
                                        print(f"      Analysis: {analysis_type} (ID: {analysis_id})")
                                        
                                        # Check if there's feedback for this analysis
                                        if analysis_id:
                                            async with session.get(
                                                f"{base_url}/api/v1/feedback/{analysis_id}",
                                                headers=auth_headers
                                            ) as feedback_response:
                                                
                                                if feedback_response.status == 200:
                                                    feedback_data = await feedback_response.json()
                                                    if feedback_data:
                                                        print(f"        ✅ Has feedback: {feedback_data.get('rating')}")
                                                    else:
                                                        print(f"        ⚠️ Feedback response is None")
                                                else:
                                                    print(f"        ❌ No feedback (status: {feedback_response.status})")
                else:
                    print(f"❌ Failed to get user ideas: {response.status}")
            
            return True
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    print("🔍 Feedback History Debug Test")
    print("=" * 40)
    
    success = asyncio.run(test_feedback_history_debug())
    
    if success:
        print("\n✅ Debug test completed successfully")
    else:
        print("\n❌ Debug test failed") 