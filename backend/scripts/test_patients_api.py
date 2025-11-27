"""Quick test script to verify patients endpoint."""

import requests

try:
    print("Testing GET /api/patients...")
    response = requests.get("http://localhost:8000/api/patients", timeout=5)
    
    print(f"Status: {response.status_code}")
    
    if response.ok:
        patients = response.json()
        print(f"✓ Success! Found {len(patients)} patients")
        
        if patients:
            print("\nFirst patient:")
            print(patients[0])
    else:
        print(f"✗ Error: {response.text}")
        
except requests.exceptions.Timeout:
    print("✗ Request timed out - backend might be stuck")
except requests.exceptions.ConnectionError:
    print("✗ Cannot connect - backend might not be running")
except Exception as e:
    print(f"✗ Error: {e}")
