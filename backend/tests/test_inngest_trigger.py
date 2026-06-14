"""Manual smoke script for the Inngest-backed agent assessment."""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4

import inngest

backend_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_root))

from app.inngest.client import inngest_client


async def trigger_assessment():
    assessment_id = str(uuid4())
    session_id = str(uuid4())
    await inngest_client.send(
        inngest.Event(
            name="agent/assessment.request",
            data={
                "assessment_id": assessment_id,
                "message": "Assess risk for patient P-001",
                "session_id": session_id,
                "patient_id": "P-001",
            },
            id=assessment_id,
        )
    )
    print(f"Triggered agent assessment {assessment_id}")


if __name__ == "__main__":
    asyncio.run(trigger_assessment())
