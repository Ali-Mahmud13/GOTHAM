"""Generate response using LLM."""

import logging
from app.core.llm import get_llm

logger = logging.getLogger(__name__)


def generate_response(state):
   
    user_message = state["message"]
    
    try:
        # Get the LLM
        llm = get_llm()
        
        if llm is None:
            # No API key configured
            state["response"] = (
                "LLM not configured. "
                "Add HUGGINGFACE_API_KEY to .env to use Llama-3.3-70B-Instruct. "
                f"You said: '{user_message}'"
            )
            return state
        
        # Call the LLM with user's message
        logger.info(f"Calling LLM with message: {user_message}")
        response = llm.invoke(user_message)
        
        # Extract the text content from AIMessage
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Set the actual LLM response
        state["response"] = response_text
        logger.info(f"LLM responded successfully")
        
    except Exception as e:
        logger.error(f"LLM error: {e}")
        state["response"] = f"Error calling LLM: {str(e)}"
    
    return state
