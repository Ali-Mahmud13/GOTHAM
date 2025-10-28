
import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MODEL_NAME = "llama-3.3-70b-versatile"


def get_llm():

    if not GROQ_API_KEY:
        return None
    
    from langchain_groq import ChatGroq
    
    llm = ChatGroq(
        model=MODEL_NAME,
        groq_api_key=GROQ_API_KEY,
        temperature=0.7,
        max_tokens=512,
    )
    
    return llm
