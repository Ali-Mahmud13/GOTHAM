import os
from pathlib import Path
from dotenv import load_dotenv

# Get the project root directory
project_root = Path(__file__).parent

# Load .env file from project root
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")

#rag 
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
HF_API_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")
EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"
LLM_MODEL = "mistralai/Mistral-7B-Instruct-v0.2:featherless-ai"
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
DIMENSION = 768 
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50 
MAX_CONTEXT_LENGTH = 1500
LOCAL_ID_FILE = "uploaded_vector_ids.json"