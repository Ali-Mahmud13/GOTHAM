from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from ..state import AgentState
from ..system_prompt import GENERATE_KEYWORDS_PROMPT
from config import GROQ_API_KEY, MODEL_NAME
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def generate_keywords_node(state: AgentState) -> AgentState:
    llm = ChatGroq(api_key=GROQ_API_KEY, model=MODEL_NAME, temperature=0.3)
    
    user_message = state["messages"][-1].content
    maternal_report = state.get("maternal_report", "") or "Not available"
    fetal_report = state.get("fetal_report", "") or "Not available"
    
    logger.info("="*60)
    logger.info("GENERATE KEYWORDS - Starting")
    logger.info("="*60)
    logger.info(f"User message: '{user_message}'")
    logger.info(f"Has maternal_report: {bool(state.get('maternal_report'))}")
    logger.info(f"Has fetal_report: {bool(state.get('fetal_report'))}")
    
    prompt = GENERATE_KEYWORDS_PROMPT.format(
        user_message=user_message,
        maternal_report=maternal_report,
        fetal_report=fetal_report
    )
    
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    keywords = response.content.strip()
    
    logger.info(f"Generated keywords: {keywords}")
    logger.info("="*60 + "\n")
    
    # Store keywords in state for RAG retrieval to use
    state["rag_keywords"] = keywords
    
    return state