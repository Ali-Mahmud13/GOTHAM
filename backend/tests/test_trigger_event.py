"""Test script to trigger Inngest function."""

import requests
import json


def trigger_test_event():
    """Send a test event to the Inngest dev server."""
    
    event = {
        "name": "app/my_function",
        "data": {
            "message": "Hello from test!"
        }
    }
    
    # Send to Inngest dev server
    response = requests.post(
        "http://localhost:8288/e/local",
        headers={"Content-Type": "application/json"},
        data=json.dumps(event)
    )
    
    if response.status_code == 200:
        print("✅ Event sent successfully!")
        print(f"Event name: {event['name']}")
        print(f"Event data: {event['data']}")
        print("\nCheck http://localhost:8288 to see the function run!")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)


if __name__ == "__main__":
    trigger_test_event()

