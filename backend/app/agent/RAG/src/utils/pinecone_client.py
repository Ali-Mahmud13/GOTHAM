import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec, PineconeApiException
import time

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "rag-fyp-medical")
DIMENSION = 768

# Global Pinecone client and index
pc = None
index = None

def initialize_pinecone():
    """Initializes the Pinecone client and index, and returns the index."""
    global pc, index
    if index:
        return index

    if not PINECONE_API_KEY or not PINECONE_ENVIRONMENT:
        raise ValueError("PINECONE_API_KEY and PINECONE_ENVIRONMENT must be set.")

    try:
        print("🌲 Initializing Pinecone client...")
        pc = Pinecone(api_key=PINECONE_API_KEY)

        if INDEX_NAME not in [idx['name'] for idx in pc.list_indexes()]:
            print(f"🆕 Creating Pinecone index '{INDEX_NAME}'...")
            pc.create_index(
                name=INDEX_NAME,
                dimension=DIMENSION,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region=PINECONE_ENVIRONMENT)
            )
            print("⏳ Waiting for index to be ready...")
            while not pc.describe_index(INDEX_NAME).status["ready"]:
                time.sleep(1)
            print("✅ Index created and ready.")
        else:
            print(f"✅ Using existing index: {INDEX_NAME}")

        index = pc.Index(INDEX_NAME)
        return index

    except Exception as e:
        print(f"❌ Failed to initialize Pinecone: {e}")
        return None

# Initialize on module load
initialize_pinecone()

def index_exists_and_populated() -> bool:
    """Check if the global index exists and has vectors."""
    if not index:
        print("⚠️ Pinecone index not initialized.")
        return False
    try:
        stats = index.describe_index_stats()
        total_vectors = stats.get('total_vector_count', 0)
        if total_vectors > 0:
            print(f"✅ Pinecone index has {total_vectors} vectors.")
            return True
        else:
            print("⚠️ Pinecone index is empty.")
            return False
    except PineconeApiException as e:
        print(f"❌ Error checking index stats: {e}")
        return False

# Export for reuse
__all__ = ["index", "pc", "initialize_pinecone", "index_exists_and_populated"]