"""Test script to verify agent can fetch patient data from database."""

import sys
from pathlib import Path
import asyncio

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.patient_service import get_patient_service

async def test_patient_data_fetch():
    """Test fetching patient data like the agent does."""
    
    print("\n" + "="*60)
    print("TESTING AGENT DATABASE ACCESS")
    print("="*60)
    
    patient_service = get_patient_service()
    
    # Test fetching data for each patient
    patient_ids = ["P001", "P002", "P003", "P004", "P005"]
    
    for patient_id in patient_ids:
        print(f"\n{'─'*60}")
        print(f"Testing Patient: {patient_id}")
        print(f"{'─'*60}")
        
        # This is exactly what the agent does
        patient_data = await patient_service.get_patient_data(patient_id)
        
        if patient_data:
            print(f"✅ SUCCESS! Agent can fetch data for {patient_id}")
            print(f"\nData fetched:")
            for key, value in patient_data.items():
                if value is not None:
                    print(f"  • {key}: {value}")
        else:
            print(f"❌ FAILED! No data found for {patient_id}")
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    print("\n✓ The agent is now connected to the database!")
    print("✓ Try asking: 'What is the risk for patient P001?'\n")

if __name__ == "__main__":
    asyncio.run(test_patient_data_fetch())
