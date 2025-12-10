"""LLM initialization and configuration."""

from app.core.config import (
    GROQ_API_KEY, MODEL_NAME,
    GEMINI_API_KEY, GEMINI_MODEL_NAME,
    OPENAI_API_KEY, OPENAI_MODEL_NAME,
    LLM_PROVIDER
)


def get_llm(temperature: float = 0.7, max_tokens: int = 512):
    """
    Get configured LLM instance based on LLM_PROVIDER env var.
    
    Supports: openai, groq, gemini
    
    Args:
        temperature: Sampling temperature (0-1)
        max_tokens: Maximum tokens in response
        
    Returns:
        Chat model instance
    """
    provider = LLM_PROVIDER.lower()
    
    if provider == "openai":
        from langchain_openai import ChatOpenAI
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not configured in environment variables")
        return ChatOpenAI(
            model=OPENAI_MODEL_NAME,
            api_key=OPENAI_API_KEY,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    
    elif provider == "groq":
        from langchain_groq import ChatGroq
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not configured in environment variables")
        return ChatGroq(
            model=MODEL_NAME,
            groq_api_key=GROQ_API_KEY,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    
    elif provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not configured in environment variables")
        return ChatGoogleGenerativeAI(
            model=GEMINI_MODEL_NAME,
            google_api_key=GEMINI_API_KEY,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
    
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider}. Use 'openai', 'groq', or 'gemini'")
