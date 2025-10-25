"""Example Inngest function."""

import logging
import inngest
from app.inngest.client import inngest_client

logger = logging.getLogger(__name__)


@inngest_client.create_function(
    fn_id="my_function",
    trigger=inngest.TriggerEvent(event="app/my_function"),
)
async def my_function(ctx: inngest.Context) -> dict:
    """Example function with 3 steps."""
    
    logger.info(f"Function started - Event: {ctx.event.name}")
    
    # Step 1: Fetch data
    data = await ctx.step.run(
        "fetch-data",
        lambda: f"Data from event: {ctx.event.data.get('message', 'No message')}"
    )
    logger.info(f"Step 1: {data}")
    
    # Step 2: Process data
    result = await ctx.step.run(
        "process-data",
        lambda: f"Processed: {data}"
    )
    logger.info(f"Step 2: {result}")
    
    # Step 3: Save result
    saved = await ctx.step.run(
        "save-result",
        lambda: f"Saved: {result}"
    )
    logger.info(f"Step 3: {saved}")
    
    return {
        "status": "success",
        "step1": data,
        "step2": result,
        "step3": saved
    }
