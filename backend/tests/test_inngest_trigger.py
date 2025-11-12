"""Test script to trigger Inngest background assessment."""

import asyncio
from uuid import uuid4
from app.inngest.event_sender import send_event


async def test_trigger_assessment():
    """
    Test triggering a background assessment via Inngest.
    
    Prerequisites:
        1. Inngest dev server running: npx inngest-cli@latest dev
        2. FastAPI server running: uvicorn app.main:app --reload
    """
    assessment_id = str(uuid4())
    session_id = str(uuid4())
    
    print("=" * 60)
    print("Testing Inngest Background Assessment")
    print("=" * 60)
    print(f"Assessment ID: {assessment_id}")
    print(f"Session ID: {session_id}")
    print("=" * 60)
    
    try:
        # Trigger the background assessment
        success = await send_event(
            "agent/assessment.request",
            {
                "assessment_id": assessment_id,
                "message": "Assess risk for patient P-001",
                "session_id": session_id,
                "patient_id": "P-001",
            }
        )
        
        if not success:
            raise Exception("Failed to send event")
        
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


async def test_trigger_maternal():
    """Test triggering maternal prediction."""
    assessment_id = str(uuid4())
    
    print("\nTesting Maternal Prediction...")
    print(f"Assessment ID: {assessment_id}")
    
    try:
        await send_event(
            "prediction/maternal.run",
            {
                "assessment_id": assessment_id,
                "patient_data": {
                    "age": 28,
                    "blood_sugar": 140,
                    "bmi": 27.5,
                },
                "models": ["gdp"],
            }
        )
        
        print("✓ Maternal prediction triggered!")
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")


async def test_trigger_fetal():
    """Test triggering fetal prediction."""
    assessment_id = str(uuid4())
    
    print("\nTesting Fetal Prediction...")
    print(f"Assessment ID: {assessment_id}")
    
    try:
        await send_event(
            "prediction/fetal.run",
            {
                "assessment_id": assessment_id,
                "patient_data": {
                    "heart_rate": 145,
                    "movements": 8,
                },
                "models": ["fetal_health"],
            }
        )
        
        print("✓ Fetal prediction triggered!")
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")


async def test_trigger_rag():
    """Test triggering RAG retrieval."""
    assessment_id = str(uuid4())
    
    print("\nTesting RAG Retrieval...")
    print(f"Assessment ID: {assessment_id}")
    
    try:
        await send_event(
            "rag/retrieve",
            {
                "assessment_id": assessment_id,
                "keywords": "gestational diabetes risk factors treatment",
                "query": "What are the risk factors for gestational diabetes?",
            }
        )
        
        print("✓ RAG retrieval triggered!")
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")


async def main():
    """Run all tests."""
    import sys
    
    if len(sys.argv) > 1:
        test_type = sys.argv[1]
        if test_type == "maternal":
            await test_trigger_maternal()
        elif test_type == "fetal":
            await test_trigger_fetal()
        elif test_type == "rag":
            await test_trigger_rag()
        else:
            await test_trigger_assessment()
    else:
        # Default: test full assessment
        await test_trigger_assessment()


if __name__ == "__main__":
    asyncio.run(main())

