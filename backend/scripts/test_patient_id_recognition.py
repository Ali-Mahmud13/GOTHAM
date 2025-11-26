"""Test the improved patient ID recognition."""

import requests

BASE_URL = "http://localhost:8000/api"

test_queries = [
    "P004",  # Just patient ID
    "what about patient P002",  # Follow-up style
    "assess P003",  # Brief command
]

print("\n" + "="*60)
print("TESTING IMPROVED PATIENT ID RECOGNITION")
print("="*60)

for query in test_queries:
    print(f"\n🔹 Testing: '{query}'")
    print("─"*40)
    
    response = requests.post(
        f"{BASE_URL}/chat",
        json={"message": query}
    )
    
    if response.status_code == 200:
        data = response.json()
        preview = data.get("response", "")[:200]
        
        if "could you please" in preview.lower() or "clarification" in preview.lower():
            print("❌ Still asking for clarification")
        else:
            print("✅ Recognized and processing!")
            print(f"Response preview: {preview}...")
    else:
        print(f"❌ Error: {response.status_code}")
    
print("\n" + "="*60)
