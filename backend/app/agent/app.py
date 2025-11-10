import asyncio
from langchain_core.messages import HumanMessage
from .main_agent.graph import create_graph
from uuid import uuid4

async def main():
    graph = create_graph()
    
    thread_id = str(uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    print("Antenatal Care Assistant Started")
    print("Type 'exit' or 'quit' to end the conversation\n")
    
    while True:
        user_input = input("You: ")
        
        if user_input.lower() in ['exit', 'quit']:
            print("Goodbye!")
            break
        
        if not user_input.strip():
            continue
        
        state = {
            "messages": [HumanMessage(content=user_input)]
        }
        
        result = await graph.ainvoke(state, config=config)
        
        assistant_message = result["messages"][-1].content
        print(f"\nAssistant: {assistant_message}\n")

if __name__ == "__main__":
    asyncio.run(main())
