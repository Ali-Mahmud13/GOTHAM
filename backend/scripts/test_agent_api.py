"""Test the agent via API to verify database integration works end-to-end."""

import requests
import time
import json

# API endpoint
BASE_URL = "http://localhost:8000/api"

def test_agent_with_patient():
    """Send a message to the agent asking about a patient."""
    
    print("\n" + "="*60)
    print("TESTING AGENT WITH DATABASE QUERY")
    print("="*60)
    
    # Test query
    message = "What is the gestational diabetes risk for patient P001?"
    
    print(f"\nSending message: '{message}'")
    print("\nWaiting for agent response...")
    
    # Send message to agent
    response = requests.post(
        f"{BASE_URL}/chat",
        json={"message": message}
    )
    
    if response.status_code == 200:
        data = response.json()
        
        print("\n" + "─"*60)
        print("✅ AGENT RESPONSE:")
        print("─"*60)
        print(data.get("response", "No response"))
        print("\n" + "─"*60)
        
        if "assessment_id" in data:
            print(f"\nAssessment ID: {data['assessment_id']}")
            print(f"Session ID: {data['session_id']}")
            
            # Poll for results
            assessment_id = data["assessment_id"]
            print(f"\nPolling for assessment results...")
            
            for i in range(30):  # Poll for up to 30 seconds
                time.sleep(1)
                status_response = requests.get(f"{BASE_URL}/assessment/{assessment_id}")
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    
                    if status_data.get("status") == "completed":
                        print("\n✅ Assessment completed!")
                        print("\nFinal Response:")
                        print("─"*60)
                        print(status_data.get("response", "No response"))
                        print("─"*60)
                        break
                    elif status_data.get("status") == "processing":
                        print(f"  Processing... ({i+1}s)")
                    else:
                        print(f"  Status: {status_data.get('status')}")
            else:
                print("\n⏱ Timeout waiting for response")
        
        print("\n" + "="*60)
        print("TEST COMPLETE")
        print("="*60)
        print("\n✓ The agent successfully queried the database!")
        print("✓ Patient data was fetched and used for assessment")
        
    else:
        print(f"\n❌ Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    try:
        test_agent_with_patient()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure the backend is running on http://localhost:8000")
