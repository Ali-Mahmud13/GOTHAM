from ..state import AgentState, report_progress
import logging
import sys
from pathlib import Path
# Add project root to path
project_root = Path(__file__).resolve().parents[4]  
sys.path.insert(0, str(project_root))
from app.agent.RAG.src.retriever.query_pinecone import retrieve_similar_chunks

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def rag_retrieval_node(state: AgentState) -> AgentState:
    """
    RAG retrieval node - retrieves medical literature from Pinecone based on keywords or user query.
    """
    report_progress(5, "Retrieving medical guidelines")
    
    logger.info("="*60)
    logger.info("RAG RETRIEVAL - Starting")
    logger.info("="*60)
    
    # Check if we have keywords (from generate_keywords) or use direct user input
    keywords = state.get("rag_keywords")
    user_message = state["messages"][-1].content
    
    if keywords:
        logger.info(f"Using generated keywords: {keywords}")
        query = keywords
    else:
        logger.info(f"Using direct user input: {user_message}")
        query = user_message
    
    # Retrieve chunks from Pinecone
    logger.info(f"🔍 Querying Pinecone with: '{query}'")
    chunks = retrieve_similar_chunks(query, top_k=5)
    
    if not chunks:
        logger.warning("❌ No relevant chunks found in RAG database")
        rag_context = "No relevant medical literature found for this query."
    else:
        logger.info(f"✅ Retrieved {len(chunks)} relevant chunks from Pinecone")
        # Combine chunks into context
        rag_context = "\n\n---\n\n".join(chunks)
    
    logger.info(f"RAG context generated (length: {len(rag_context)} chars)")
    logger.info("="*60 + "\n")
    print(rag_context)  # For debugging
    
    state["rag_context"] = rag_context
    
    return state