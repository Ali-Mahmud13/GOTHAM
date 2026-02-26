#!/usr/bin/env python3
"""
Quick test script to debug P001 assessment data
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.patient_service import get_patient_service
from app.agent.main_agent.tools.helper.clean_data import clean_data_for_model

async def main():
    # Get patient service
    patient_service = get_patient_service()
    
    # Fetch P001 data
    patient_data = await patient_service.get_patient_data("P001")
    
    if not patient_data:
        print("❌ No data found for P001")
        return
    
    print("=" * 80)
    print("RAW PATIENT DATA for P001:")
    print("=" * 80)
    for key, value in sorted(patient_data.items()):
        print(f"{key:40s}: {value}")
    
    print("\n" + "=" * 80)
    print("CLEANED DATA FOR GDM MODEL:")
    print("=" * 80)
    
    contract_path = backend_dir / "app/agent/main_agent/tools/maternal_health_pipeline/gdp/gdp_contract.yaml"
    cleaned_data = await clean_data_for_model(patient_data, str(contract_path))
    
    for key, value in sorted(cleaned_data.items()):
        status = "✅" if value is not None else "❌"
        print(f"{status} {key:40s}: {value}")
    
    # Check for missing
    missing = [k for k, v in cleaned_data.items() if v is None]
    if missing:
        print(f"\n❌ MISSING FIELDS: {', '.join(missing)}")
    else:
        print(f"\n✅ ALL FIELDS PRESENT - GDM Assessment should work!")

if __name__ == "__main__":
    asyncio.run(main())
