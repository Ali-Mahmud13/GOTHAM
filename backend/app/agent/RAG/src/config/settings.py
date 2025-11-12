import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
HF_API_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")

# Model Settings
## converts text into embeddings; dimension = 768; 
EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"
LLM_MODEL = "mistralai/Mistral-7B-Instruct-v0.2:featherless-ai"

# Pinecone Settings
PINECONE_INDEX_NAME = "rag-fyp-medical"
DIMENSION = 768 # Must match the output dimension of your embedding model
# 768 dimensions means every piece of text is converted into a 768-length numeric vector capturing its meaning in semantic space.

# Processing Settings
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50 # Prevents losing meaning at chunk boundaries
MAX_CONTEXT_LENGTH = 1500

# Local file to track uploaded vector IDs
LOCAL_ID_FILE = "uploaded_vector_ids.json"