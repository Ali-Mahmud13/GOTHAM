"""
Test the optimized patient data retrieval method.
"""

import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

# Must be run from venv or wherever SQLModel is available
import sys
sys.path.insert(0, '/Users/abdullahmahmud/Desktop/Ali_Work/GOTHAM/backend')

from app.services.patient_service import PatientService

async def test_optimized():
    """Test optimized vs old method."""
    service = PatientService()
    
    test_patients = ["P001", "P004", "P007"]
    
    for patient_id in test_patients:
        print(f"\n{'='*60}")
        print(f"Testing patient: {patient_id}")
        print(f"{'='*60}")
        
        try:
            # Test optimized method
            data = await service.get_patient_data_optimized(patient_id)
            
            if data:
                print(f"✓ Found patient: {data.get('name')}")
                print(f"  Fields returned: {len(data)}")
                print(f"  Sample data:")
                
                if 'glucose_level' in data:
                    print(f"    GDM glucose: {data['glucose_level']}")
                if 'HGB' in data:
                    print(f"    Anemia HGB: {data['HGB']}")
                if 'fetal_heart_rate_baseline' in data:
                    print(f"    Fetal HR: {data['fetal_heart_rate_baseline']}")
            else:
                print("  ✗ No data returned")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_optimized())
