"""CLI runner for the medical agent - for testing and development."""

import asyncio
import sys
from langchain_core.messages import HumanMessage
from .main_agent.graph import create_graph
from uuid import uuid4


async def run_direct():
    """Run the agent directly (without Inngest)."""
    graph = create_graph()
    
    thread_id = str(uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    print("=" * 60)
    print("Antenatal Care Assistant - CLI Mode (Direct)")
    print("=" * 60)
    print("Type 'exit' or 'quit' to end the conversation\n")
    
    while True:
        user_input = input("You: ")
        
        if user_input.lower() in ['exit', 'quit']:
            print("\nGoodbye!")
            break
        
        if not user_input.strip():
            continue
        
        state = {
            "messages": [HumanMessage(content=user_input)]
        }
        
        print("\n[Processing...]\n")
        
        try:
            result = await graph.ainvoke(state, config=config)
            assistant_message = result["messages"][-1].content
            print(f"Assistant: {assistant_message}\n")
        except Exception as e:
            print(f"Error: {str(e)}\n")


async def run_inngest():
    """Run the agent via Inngest background jobs."""
    from app.inngest.event_sender import send_event
    
    thread_id = str(uuid4())
    
    print("=" * 60)
    print("Antenatal Care Assistant - CLI Mode (Inngest)")
    print("=" * 60)
    print("⚠️  Make sure Inngest dev server is running!")
    print("   Run: npx inngest-cli@latest dev")
    print("   Dashboard: http://localhost:8288")
    print("=" * 60)
    print("Type 'exit' or 'quit' to end the conversation\n")
    
    while True:
        user_input = input("You: ")
        
        if user_input.lower() in ['exit', 'quit']:
            print("\nGoodbye!")
            break
        
        if not user_input.strip():
            continue
        
        assessment_id = str(uuid4())
        
        print(f"\n[Triggering background assessment: {assessment_id}]\n")
        
        try:
            # Trigger Inngest event
            success = await send_event(
                "agent/assessment.request",
                {
                    "assessment_id": assessment_id,
                    "message": user_input,
                    "session_id": thread_id,
                    "patient_id": "CLI-TEST",
                }
            )
            
            if not success:
                print("Error: Failed to send event to Inngest")
                print("Make sure Inngest dev server is running!\n")
                continue
            
            print(f"✓ Assessment triggered successfully!")
            print(f"  Assessment ID: {assessment_id}")
            print(f"  Check Inngest dashboard: http://localhost:8288")
            print(f"  (Results will appear in the dashboard)\n")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            print("Make sure Inngest dev server is running!\n")


async def main():
    """Main CLI entry point."""
    # Check if user wants Inngest mode
    if len(sys.argv) > 1 and sys.argv[1] == "--inngest":
        await run_inngest()
    else:
        await run_direct()


if __name__ == "__main__":
    asyncio.run(main())
