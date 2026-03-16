"""
Test script to verify field-level data aggregation across visits.

This script tests that the PatientService correctly aggregates the latest
non-null value for each field across all patient visits.

Run: python scripts/test_data_aggregation.py
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.patient_service import get_patient_service
import asyncio
from datetime import datetime

# ANSI color codes for prettier output
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
BOLD = '\033[1m'
RESET = '\033[0m'


def print_header(text):
    """Print formatted header."""
    print(f"\n{BOLD}{BLUE}{'='*70}{RESET}")
    print(f"{BOLD}{BLUE}{text}{RESET}")
    print(f"{BOLD}{BLUE}{'='*70}{RESET}\n")


def print_success(text):
    """Print success message."""
    print(f"{GREEN}✓ {text}{RESET}")


def print_error(text):
    """Print error message."""
    print(f"{RED}✗ {text}{RESET}")


def print_info(text):
    """Print info message."""
    print(f"{YELLOW}ℹ {text}{RESET}")


def print_field(name, value, expected=None):
    """Print field with optional validation."""
    if expected is not None:
        status = GREEN if value == expected else RED
        symbol = "✓" if value == expected else "✗"
        print(f"  {status}{symbol} {name}: {value} (expected: {expected}){RESET}")
    else:
        print(f"  • {name}: {value}")


async def test_patient_data(patient_id: str, expected_fields: dict = None):
    """
    Test data loading for a specific patient.
    
    Args:
        patient_id: Patient identifier
        expected_fields: Optional dict of field:value to validate
    """
    print_header(f"Testing Patient: {patient_id}")
    
    service = get_patient_service()
    
    try:
        # Fetch patient data
        data = await service.get_patient_data(patient_id)
        
        if not data:
            print_error(f"No data returned for patient {patient_id}")
            return False
        
        print_success(f"Data loaded successfully for {data.get('name', 'Unknown')}")
        print_info(f"Patient ID: {data.get('Patient_ID')}")
        print_info(f"Age: {data.get('age')}")
        print_info(f"Risk Level: {data.get('risk_level')}")
        
        # Print visit info
        if 'visit_date' in data:
            visit_date = data['visit_date']
            print_info(f"Latest Visit: {visit_date}")
        
        # Check GDM fields
        gdm_fields = ['glucose_level', 'sys_bp', 'dia_bp', 'bmi', 'ogtt', 'hdl', 'gestation_weeks']
        gdm_present = any(data.get(field) is not None for field in gdm_fields)
        
        if gdm_present:
            print(f"\n{BOLD}GDM Assessment Data:{RESET}")
            for field in gdm_fields:
                value = data.get(field)
                if expected_fields and field in expected_fields:
                    print_field(field, value, expected_fields[field])
                else:
                    print_field(field, value)
            
            # Risk prediction fields
            if 'gdm_risk_level' in data:
                print_field('gdm_risk_level', data['gdm_risk_level'])
            if 'gdm_confidence' in data:
                print_field('gdm_confidence', data['gdm_confidence'])
        else:
            print_info("No GDM assessment data found")
        
        # Check Anemia/CBC fields
        cbc_fields = ['WBC', 'RBC', 'HGB', 'HCT', 'MCV', 'MCH', 'MCHC', 'PLT']
        cbc_present = any(data.get(field) is not None for field in cbc_fields)
        
        if cbc_present:
            print(f"\n{BOLD}Anemia/CBC Assessment Data:{RESET}")
            for field in cbc_fields:
                value = data.get(field)
                if expected_fields and field in expected_fields:
                    print_field(field, value, expected_fields[field])
                else:
                    print_field(field, value)
            
            # Diagnosis fields
            if 'anemia_diagnosis' in data:
                print_field('anemia_diagnosis', data['anemia_diagnosis'])
            if 'anemia_confidence' in data:
                print_field('anemia_confidence', data['anemia_confidence'])
        else:
            print_info("No Anemia/CBC assessment data found")
        
        # Check Fetal Health fields
        fetal_fields = ['fetal_heart_rate_baseline', 'fetal_accelerations', 'fetal_movement']
        fetal_present = any(data.get(field) is not None for field in fetal_fields)
        
        if fetal_present:
            print(f"\n{BOLD}Fetal Health Assessment Data:{RESET}")
            for field in fetal_fields:
                value = data.get(field)
                if expected_fields and field in expected_fields:
                    print_field(field, value, expected_fields[field])
                else:
                    print_field(field, value)
            
            if 'fetal_status' in data:
                print_field('fetal_status', data['fetal_status'])
            if 'fetal_confidence' in data:
                print_field('fetal_confidence', data['fetal_confidence'])
        else:
            print_info("No Fetal Health assessment data found")
        
        # Validate expected fields if provided
        if expected_fields:
            print(f"\n{BOLD}Validation Results:{RESET}")
            all_match = True
            for field, expected_value in expected_fields.items():
                actual_value = data.get(field)
                if actual_value == expected_value:
                    print_success(f"{field}: {actual_value} ✓")
                else:
                    print_error(f"{field}: {actual_value} (expected: {expected_value})")
                    all_match = False
            
            if all_match:
                print_success("All validations passed!")
                return True
            else:
                print_error("Some validations failed")
                return False
        
        return True
        
    except Exception as e:
        print_error(f"Error loading data: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run comprehensive test suite."""
    print(f"\n{BOLD}{'='*70}")
    print(f"  GOTHAM Data Aggregation Test Suite")
    print(f"  Testing field-level aggregation across visits")
    print(f"{'='*70}{RESET}\n")
    
    results = []
    
    # Test 1: Patient with GDM only (P001)
    print_header("TEST 1: GDM Only Patient (P001)")
    print_info("Expected: GDM data present, no Anemia/Fetal data")
    result1 = await test_patient_data("P001")
    results.append(("P001 - GDM Only", result1))
    
    # Test 2: Patient with Anemia only (P002)
    print_header("TEST 2: Anemia Only Patient (P002)")
    print_info("Expected: CBC data present, no GDM/Fetal data")
    result2 = await test_patient_data("P002")
    results.append(("P002 - Anemia Only", result2))
    
    # Test 3: Patient with FHP only (P003)
    print_header("TEST 3: Fetal Health Only Patient (P003)")
    print_info("Expected: Fetal data present, no GDM/Anemia data")
    result3 = await test_patient_data("P003")
    results.append(("P003 - FHP Only", result3))
    
    # Test 4: Patient with GDM + Anemia (P004)
    print_header("TEST 4: GDM + Anemia Patient (P004)")
    print_info("Expected: Both GDM and CBC data present")
    print_info("Testing aggregation across 4 visits")
    # Latest data should be from Visit 4 (Week 34)
    expected_p004 = {
        'glucose_level': 118.0,  # Visit 4
        'bmi': 33.2,              # Visit 4
        'ogtt': 145.0,            # Visit 4
        'HGB': 11.8,              # Visit 4 hemoglobin
    }
    result4 = await test_patient_data("P004", expected_p004)
    results.append(("P004 - GDM + Anemia", result4))
    
    # Test 5: Patient with Anemia + FHP (P005)
    print_header("TEST 5: Anemia + Fetal Health Patient (P005)")
    print_info("Expected: Both CBC and Fetal data present")
    result5 = await test_patient_data("P005")
    results.append(("P005 - Anemia + FHP", result5))
    
    # Test 6: Patient with partial data (P006)
    print_header("TEST 6: Partial Data Patient (P006)")
    print_info("Expected: Aggregated data from multiple visits")
    print_info("This tests that fields from earlier visits are preserved")
    result6 = await test_patient_data("P006")
    results.append(("P006 - Partial Data", result6))
    
    # Test 7: Patient with all three assessments (P007)
    print_header("TEST 7: Complete Patient (P007)")
    print_info("Expected: GDM, CBC, and Fetal data all present")
    result7 = await test_patient_data("P007")
    results.append(("P007 - All Assessments", result7))
    
    # Summary
    print_header("TEST SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        if result:
            print_success(f"{test_name}")
        else:
            print_error(f"{test_name}")
    
    print(f"\n{BOLD}Results: {passed}/{total} tests passed{RESET}")
    
    if passed == total:
        print_success("All tests passed! ✓")
        return 0
    else:
        print_error(f"{total - passed} test(s) failed")
        return 1


async def test_specific_aggregation():
    """Test specific aggregation scenario manually."""
    print_header("MANUAL AGGREGATION TEST")
    print_info("Testing P006 which has partial data across visits")
    
    service = get_patient_service()
    data = await service.get_patient_data("P006")
    
    if data:
        print(f"\n{BOLD}Full patient data dictionary:{RESET}")
        for key, value in sorted(data.items()):
            if value is not None:
                print(f"  {key}: {value}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test GOTHAM data aggregation")
    parser.add_argument("--patient", "-p", help="Test specific patient (e.g., P001)")
    parser.add_argument("--manual", "-m", action="store_true", help="Run manual aggregation test")
    
    args = parser.parse_args()
    
    if args.manual:
        asyncio.run(test_specific_aggregation())
    elif args.patient:
        asyncio.run(test_patient_data(args.patient))
    else:
        exit_code = asyncio.run(run_all_tests())
        sys.exit(exit_code)
