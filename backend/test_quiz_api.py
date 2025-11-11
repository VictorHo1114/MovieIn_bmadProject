"""
Test Quiz API
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

# Step 1: Login to get token
print("=" * 60)
print("Step 1: Login")
print("=" * 60)

login_data = {
    "email": "quiz_test@example.com",
    "password": "quiz123456"
}

response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    token_data = response.json()
    access_token = token_data.get("access_token")
    print(f"✅ Login successful!")
    print(f"Token: {access_token[:50]}...")
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    # Step 2: Get today's quiz
    print("\n" + "=" * 60)
    print("Step 2: Get Today's Quiz")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/api/v1/quiz/today", headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        quiz_data = response.json()
        print(f"✅ Quiz retrieved successfully!")
        print(json.dumps(quiz_data, indent=2, ensure_ascii=False))
        
        if not quiz_data.get("has_answered") and quiz_data.get("quiz"):
            quiz_id = quiz_data["quiz"]["id"]
            
            # Step 3: Submit answer
            print("\n" + "=" * 60)
            print("Step 3: Submit Answer")
            print("=" * 60)
            
            submit_data = {
                "quiz_id": quiz_id,
                "answer": 1,  # Answer B (correct answer for Inception quiz)
                "time_spent": 15
            }
            
            response = requests.post(
                f"{BASE_URL}/api/v1/quiz/submit",
                json=submit_data,
                headers=headers
            )
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Answer submitted!")
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print(f"❌ Submit failed: {response.text}")
        else:
            print("⚠️ Already answered today or no quiz available")
    else:
        print(f"❌ Failed to get quiz: {response.text}")
    
    # Step 4: Get quiz history
    print("\n" + "=" * 60)
    print("Step 4: Get Quiz History")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/api/v1/quiz/history?limit=5", headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        history = response.json()
        print(f"✅ History retrieved!")
        print(f"Total attempts: {history['stats']['total_attempts']}")
        print(f"Correct: {history['stats']['correct_count']}")
        print(f"Accuracy: {history['stats']['accuracy_rate']}%")
        print(f"Streak: {history['stats']['streak_days']} days")
    else:
        print(f"❌ Failed to get history: {response.text}")
        
else:
    print(f"❌ Login failed: {response.text}")
    print("\n💡 Please create a test user first or update the credentials above")
