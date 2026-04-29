"""
Debug agent workflow to find CBC data issue.
"""

import asyncio
import sys
sys.path.insert(0, '/Users/abdullahmahmud/Desktop/Ali_Work/GOTHAM/backend')

from app.services.patient_service import PatientService

async def debug_workflow():
    """Trace the exact data flow."""
    
    print("="*70)
    print("DEBUGGING AGENT WORKFLOW FOR P007")
    print("="*70)
    
    service = PatientService()
    
    print("\n1. Calling get_patient_data_optimized('P007')...")
    patient_data = await service.get_patient_data_optimized("P007")
    
    print("\n2. Returned patient_data keys:")
    print(f"   Total fields: {len(patient_data)}")
    
    # Check CBC fields specifically
    cbc_fields = ['WBC', 'RBC', 'HGB', 'HCT', 'MCV', 'MCH', 'MCHC', 'PLT']
    print("\n3. CBC Fields in response:")
    for field in cbc_fields:
        value = patient_data.get(field)
        print(f"   {field}: {value}")
    
    # Check if lowercase versions exist
    print("\n4. Checking lowercase versions:")
    for field in cbc_fields:
        value = patient_data.get(field.lower())
        print(f"   {field.lower()}: {value}")
    
    # Check all keys containing 'bc' or 'hemo'
    print("\n5. All keys containing 'bc' or 'hemo':")
    matching_keys = [k for k in patient_data.keys() if 'bc' in k.lower() or 'hemo' in k.lower()]
    for key in matching_keys:
        print(f"   {key}: {patient_data[key]}")
    
    print("\n6. Sample of all returned fields:")
    for i, (key, value) in enumerate(list(patient_data.items())[:15]):
        print(f"   {key}: {value}")
    
    print("\n" + "="*70)
    print("DIAGNOSIS:")
    
    cbc_present = any(patient_data.get(f) is not None for f in cbc_fields)
    if cbc_present:
        print("✅ CBC data IS being returned correctly")
    else:
        print("❌ CBC data is NOT in the response")
        print("   Check if response builder is mapping correctly")

if __name__ == "__main__":
    asyncio.run(debug_workflow())
