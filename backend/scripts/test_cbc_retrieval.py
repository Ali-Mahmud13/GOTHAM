#!/usr/bin/env python3
"""Test patient data retrieval with CBC fields"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import asyncio
from app.services.patient_service import PatientService

async def test_patient_data():
    print("="*70)
    print("TESTING PATIENT DATA RETRIEVAL FOR P007")
    print("="*70)
    
    service = PatientService()
    data = await service.get_patient_data_optimized("P007")
    
    print(f"\n📊 Total fields returned: {len(data)}")
    
    print("\n🩸 CBC FIELDS:")
    cbc_fields = ['WBC', 'RBC', 'HGB', 'HCT', 'MCV', 'MCH', 'MCHC', 'PLT']
    for field in cbc_fields:
        value = data.get(field)
        status = "✅" if value is not None else "❌"
        print(f"  {status} {field}: {value}")
    
    print("\n🍬 GDM FIELDS:")
    gdm_fields = ['glucose_level', 'sys_bp', 'dia_bp', 'bmi', 'ogtt']
    for field in gdm_fields:
        value = data.get(field)
        status = "✅" if value is not None else "⚪"
        print(f"  {status} {field}: {value}")
    
    # Summary
    cbc_found = sum(1 for f in cbc_fields if data.get(f) is not None)
    print(f"\n📋 SUMMARY: {cbc_found}/{len(cbc_fields)} CBC fields populated")
    
    return cbc_found == len(cbc_fields)

if __name__ == "__main__":
    success = asyncio.run(test_patient_data())
    sys.exit(0 if success else 1)
