"""RAG pipeline settings for ingestion scripts."""
import os
from pathlib import Path
from dotenv import load_dotenv

project_root = Path(__file__).resolve().parents[6]
load_dotenv(dotenv_path=project_root / ".env")

EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"
DIMENSION = 768
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
MAX_CONTEXT_LENGTH = 1500
LOCAL_ID_FILE = "uploaded_vector_ids.json"

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
