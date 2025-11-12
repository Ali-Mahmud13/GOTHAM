"""Test script to trigger Inngest background assessment.

Uses official Inngest SDK: inngest_client.send(inngest.Event(...))

Run with:
    cd backend
    python tests/test_inngest_trigger.py

Prerequisites:
    1. Inngest dev server: npx inngest-cli@latest dev
    2. FastAPI server: uvicorn app.main:app --reload
"""

import asyncio
import inngest
from uuid import uuid4
from app.inngest.client import inngest_client


async def test_trigger_assessment():
    """Test triggering a background assessment via Inngest."""
    assessment_id = str(uuid4())
    session_id = str(uuid4())
    
    print("=" * 60)
    print("Testing Inngest Background Assessment")
    print("=" * 60)
    print(f"Assessment ID: {assessment_id}")
    print(f"Session ID: {session_id}")
    print("=" * 60)
    
    try:
        # Trigger the background assessment using official SDK
        await inngest_client.send(
            inngest.Event(
                name="agent/assessment.request",
                data={
                    "assessment_id": assessment_id,
                    "message": "Assess risk for patient P-001",
                    "session_id": session_id,
                    "patient_id": "P-001",
                },
                id=assessment_id
            )
        )
        
        print("\n✓ Successfully triggered background assessment!")
        print("\nNext steps:")
        print("  1. Open Inngest dashboard: http://localhost:8288")
        print("  2. Look for function: 'agent-assessment'")
        print(f"  3. Find your assessment ID: {assessment_id}")
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        print("\nMake sure:")
        print("  1. Inngest dev server is running")
        print("     Run: npx inngest-cli@latest dev")
        print("  2. FastAPI server is running")
        print("     Run: uvicorn app.main:app --reload")
        print("\n" + "=" * 60)
        raise


async def test_trigger_risk_processing():
    """Test triggering risk processing example."""
    job_id = str(uuid4())
    
    print("\n" + "=" * 60)
    print("Testing Risk Processing Function")
    print("=" * 60)
    print(f"Job ID: {job_id}")
    print("=" * 60)
    
    try:
        await inngest_client.send(
            inngest.Event(
                name="risk/process",
                data={
                    "job_id": job_id,
                    "model": "gdp_risk",
                    "features": {
                        "age": 28,
                        "blood_sugar": 140,
                        "bmi": 27.5,
                    }
                },
                id=job_id
            )
        )
        
        print("\n✓ Risk processing triggered!")
        print(f"Check dashboard for job: {job_id}")
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        print("\n" + "=" * 60)
        raise


async def main():
    """Run tests."""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "risk":
        await test_trigger_risk_processing()
    else:
        # Default: test agent assessment
        await test_trigger_assessment()


if __name__ == "__main__":
    asyncio.run(main())

