import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from pinecone.exceptions import PineconeApiException

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "rag-fyp-medical")

# Initialize Pinecone client
pc = Pinecone(api_key=PINECONE_API_KEY)

# Function to safely create index if it doesn't exist
def ensure_index_exists(index_name: str, dimension: int = 768):
    try:
        existing_indexes = pc.list_indexes()
        if index_name not in existing_indexes:
            print(f"🆕 Creating Pinecone index: {index_name}")
            pc.create_index(
                name=index_name,
                dimension=dimension,
                metric="cosine", # Cosine similarity measures how similar two vectors are by calculating the cosine of the angle between them.
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )
        else:
            print(f"✅ Pinecone index '{index_name}' already exists")
    except PineconeApiException as e:
        if e.status == 409:  # ALREADY_EXISTS
            print(f"⚠️ Index '{index_name}' already exists (409), skipping creation")
        else:
            raise e

# Ensure our index exists before connecting
ensure_index_exists(INDEX_NAME)

# Get reference to the index
index = pc.Index(INDEX_NAME)

# Utility to check if index has vectors (prevents re-embedding if populated)
def index_exists_and_populated(index_name: str = None) -> bool:
    idx = index if index_name is None else pc.Index(index_name)
    try:
        stats = idx.describe_index_stats()
        total_vectors = stats.get('total_vector_count', 0)
        if total_vectors > 0:
            print(f"✅ Pinecone index has {total_vectors} vectors")
            return True
        else:
            print("⚠️ Pinecone index is empty")
            return False
    except Exception as e:
        print(f"❌ Error checking index stats: {e}")
        return False

# Export for reuse
__all__ = ["index", "pc", "INDEX_NAME", "index_exists_and_populated"]
