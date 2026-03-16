"""
Simplified test script using HTTP requests to test data aggregation.

Run: python3 scripts/test_data_via_api.py
"""

import requests
import json

# ANSI colors
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
BOLD = '\033[1m'
RESET = '\033[0m'

BASE_URL = "http://localhost:8000"


def print_header(text):
    print(f"\n{BOLD}{BLUE}{'='*70}{RESET}")
    print(f"{BOLD}{BLUE}{text}{RESET}")
    print(f"{BOLD}{BLUE}{'='*70}{RESET}\n")


def print_success(text):
    print(f"{GREEN}✓ {text}{RESET}")


def print_error(text):
    print(f"{RED}✗ {text}{RESET}")


def print_info(text):
    print(f"{YELLOW}ℹ {text}{RESET}")


def test_patient_via_agent(patient_id):
    """Test patient data by asking the agent."""
    print_header(f"Testing Patient {patient_id} via Agent")
    
    # Send message to agent asking for patient data
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": f"Show me all the data you have for patient {patient_id}. List every field and value.",
                "session_id": f"test_{patient_id}"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Got response for {patient_id}")
            print(f"\n{BOLD}Agent Response:{RESET}")
            print(data.get("response", "No response"))
            return True
        else:
            print_error(f"API returned status {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_dashboard_data():
    """Test dashboard endpoint to see all patients."""
    print_header("Testing Dashboard Endpoint")
    
    try:
        response = requests.get(f"{BASE_URL}/api/dashboard/overview")
        
        if response.status_code == 200:
            data = response.json()
            print_success("Dashboard data retrieved")
            print(f"\n{BOLD}Dashboard Stats:{RESET}")
            print(f"  Total Patients: {data.get('total_patients', 'N/A')}")
            print(f"  High Risk: {data.get('high_risk_count', 'N/A')}")
            print(f"  Medium Risk: {data.get('medium_risk_count', 'N/A')}")
            print(f"  Low Risk: {data.get('low_risk_count', 'N/A')}")
            
            if 'recent_assessments' in data:
                print(f"\n {BOLD}Recent Assessments:{RESET}")
                for assessment in data['recent_assessments'][:5]:
                    print(f"  • {assessment.get('patient_name')} - {assessment.get('date')}")
            
            return True
        else:
            print_error(f"API returned status {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def main():
    print(f"\n{BOLD}{'='*70}")
    print("  GOTHAM Data Aggregation API Test")
    print(f"{'='*70}{RESET}\n")
    
    print_info("Testing if backend is running...")
    try:
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code == 200:
            print_success("Backend is running!")
        else:
            print_error("Backend not responding correctly")
            return
    except:
        print_error("Backend is not running! Start it with: uvicorn app.main:app --reload")
        return
    
    # Test dashboard
    test_dashboard_data()
    
    # Test specific patients
    test_patients = ["P001", "P002", "P004", "P006"]
    
    for patient_id in test_patients:
        test_patient_via_agent(patient_id)
        print("\n" + "-"*70)
    
    print_header("Test Complete")
    print_info("Check the agent responses above to verify data aggregation")


if __name__ == "__main__":
    main()
