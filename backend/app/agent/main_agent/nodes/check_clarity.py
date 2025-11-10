from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from ..state import AgentState
from ..system_prompt import COMPLETENESS_CHECK_PROMPT, SCOPE_CHECK_PROMPT, CLARITY_CHECK_PROMPT
from config import GROQ_API_KEY, MODEL_NAME
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def check_clarity_node(state: AgentState) -> AgentState:
    llm = ChatGroq(api_key=GROQ_API_KEY, model=MODEL_NAME, temperature=0)
    
    user_message = state["messages"][-1].content
    logger.info(f"Starting clarity check for message: '{user_message}'")
    
    conversation_history = "\n".join([
        f"{'User' if isinstance(msg, HumanMessage) else 'Assistant'}: {msg.content}"
        for msg in state["messages"][:-1]
    ])
    
    # Check 1: Completeness
    logger.info("Step 1: Checking completeness...")
    completeness_prompt = COMPLETENESS_CHECK_PROMPT.format(
        conversation_history=conversation_history,
        user_message=user_message
    )
    completeness_response = await llm.ainvoke([HumanMessage(content=completeness_prompt)])
    is_complete = completeness_response.content.strip().lower() == "yes"
    state["incomplete"] = "no" if is_complete else "yes"
    logger.info(f"Completeness check result: incomplete = {state['incomplete']}")
    
    if not is_complete:
        logger.warning("Message is incomplete. Skipping remaining checks.")
        return state
    
    # Check 2: Scope
    logger.info("Step 2: Checking scope...")
    scope_prompt = SCOPE_CHECK_PROMPT.format(
        conversation_history=conversation_history,
        user_message=user_message
    )
    scope_response = await llm.ainvoke([HumanMessage(content=scope_prompt)])
    state["inscope"] = scope_response.content.strip().lower()
    logger.info(f"Scope check result: inscope = {state['inscope']}")
    
    if state["inscope"] == "no":
        logger.warning("Message is out of scope. Skipping clarity check.")
        return state
    
    # Check 3: Clarity
    logger.info("Step 3: Checking clarity...")
    clarity_prompt = CLARITY_CHECK_PROMPT.format(
        conversation_history=conversation_history,
        user_message=user_message
    )
    clarity_response = await llm.ainvoke([HumanMessage(content=clarity_prompt)])
    state["clear"] = clarity_response.content.strip().lower()
    logger.info(f"Clarity check result: clear = {state['clear']}")
    
    logger.info(f"Final clarity state - incomplete: {state['incomplete']}, inscope: {state['inscope']}, clear: {state['clear']}")
    
    return state