"""LLM initialization and configuration."""

from langchain_groq import ChatGroq
from app.core.config import GROQ_API_KEY, MODEL_NAME


def get_llm(temperature: float = 0.7, max_tokens: int = 512):
    """
    Get configured LLM instance.
    
    Args:
        temperature: Sampling temperature (0-1)
        max_tokens: Maximum tokens in response
        
    Returns:
        ChatGroq instance or None if API key not configured
    """
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not configured in environment variables")
    
    llm = ChatGroq(
        model=MODEL_NAME,
        groq_api_key=GROQ_API_KEY,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    
    return llm
