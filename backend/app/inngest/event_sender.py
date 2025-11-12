"""Helper to send Inngest events."""

import httpx
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Inngest dev server URL
INNGEST_DEV_URL = "http://localhost:8288/e/local"


async def send_event(event_name: str, event_data: Dict[str, Any]) -> bool:
    """
    Send an event to Inngest.
    
    Args:
        event_name: Name of the event (e.g., "agent/assessment.request")
        event_data: Event data dictionary
        
    Returns:
        True if successful, False otherwise
    """
    event = {
        "name": event_name,
        "data": event_data
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                INNGEST_DEV_URL,
                json=event,
                headers={"Content-Type": "application/json"},
                timeout=10.0
            )
            
            if response.status_code == 200:
                logger.info(f"Event sent successfully: {event_name}")
                return True
            else:
                logger.error(f"Failed to send event: {response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"Error sending event: {str(e)}")
        return False

