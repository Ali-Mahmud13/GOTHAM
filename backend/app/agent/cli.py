"""CLI runner for the medical agent - for testing and development."""

import asyncio
from langchain_core.messages import HumanMessage
from .main_agent.graph import create_graph
from uuid import uuid4


async def main():
    """Run the agent in CLI mode."""
    graph = create_graph()
    
    thread_id = str(uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    print("=" * 60)
    print("Antenatal Care Assistant - CLI Mode")
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


if __name__ == "__main__":
    asyncio.run(main())


