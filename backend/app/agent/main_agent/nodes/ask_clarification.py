from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from ..state import AgentState
from ..system_prompt import SYSTEM_PROMPT, CLARIFICATION_PROMPT
from config import GROQ_API_KEY, MODEL_NAME

async def ask_clarification_node(state: AgentState) -> AgentState:
    llm = ChatGroq(api_key=GROQ_API_KEY, model=MODEL_NAME, temperature=0.3)
    
    user_message = state["messages"][-1].content
    
    conversation_history = "\n".join([
        f"{'User' if isinstance(msg, HumanMessage) else 'Assistant'}: {msg.content}"
        for msg in state["messages"][:-1]
    ])
    
    # Determine what the actual issue is
    incomplete = state.get("incomplete", "no")
    inscope = state.get("inscope", "yes")
    clear = state.get("clear", "yes")
    
    out_of_scope = "yes" if inscope == "no" else "no"
    unclear = "yes" if clear == "no" else "no"
    
    clarification_prompt = CLARIFICATION_PROMPT.format(
        user_message=user_message,
        conversation_history=conversation_history,
        incomplete=incomplete,
        out_of_scope=out_of_scope,
        unclear=unclear
    )
    
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=clarification_prompt)
    ]
    
    response = await llm.ainvoke(messages)
    
    state["messages"].append(AIMessage(content=response.content))
    
    return state