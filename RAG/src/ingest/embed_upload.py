# src/ingest/embed_upload.py
import os
import json
import time
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
from src.config.settings import (
    PINECONE_API_KEY, PINECONE_ENVIRONMENT,
    PINECONE_INDEX_NAME, DIMENSION, EMBEDDING_MODEL
)

LOCAL_ID_FILE = "uploaded_vector_ids.json"  # store uploaded vector IDs locally


def initialize_pinecone():
    """Initialize Pinecone client and create index if missing."""
    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        existing_indexes = [idx["name"] for idx in pc.list_indexes()]
        if PINECONE_INDEX_NAME not in existing_indexes:
            print(f"🆕 Creating Pinecone index: {PINECONE_INDEX_NAME}")
            pc.create_index(
                name=PINECONE_INDEX_NAME,
                dimension=DIMENSION,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region=PINECONE_ENVIRONMENT)
            )
            print("⏳ Waiting for index to be ready...")
            while not pc.describe_index(PINECONE_INDEX_NAME).status["ready"]:
                time.sleep(1)
            print(f"✅ Created index: {PINECONE_INDEX_NAME}")
        else:
            print(f"✅ Using existing index: {PINECONE_INDEX_NAME}")
        return pc.Index(PINECONE_INDEX_NAME)
    except Exception as e:
        print(f"❌ Error initializing Pinecone: {e}")
        return None


def load_uploaded_ids():
    """Load locally stored uploaded vector IDs."""
    if os.path.exists(LOCAL_ID_FILE):
        with open(LOCAL_ID_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_uploaded_ids(vector_ids):
    """Save uploaded vector IDs to local JSON file."""
    with open(LOCAL_ID_FILE, "w") as f:
        json.dump(list(vector_ids), f)


def create_embeddings(chunks, existing_ids):
    """Create embeddings only for new chunks."""
    print("🧠 Loading embedding model...")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print(f"✅ Loaded model: {EMBEDDING_MODEL}")

    vectors = []
    new_ids = set()

    for chunk in tqdm(chunks, desc="Creating embeddings"):
        vector_id = f"{chunk['source'].replace('/', '_')}_{chunk['chunk_id']}"
        if vector_id in existing_ids:
            continue  # skip already uploaded
        emb = model.encode(chunk["content"], normalize_embeddings=True)
        vectors.append({
            "id": vector_id,
            "values": emb.tolist(),
            "metadata": {
                "source": chunk["source"],
                "chunk_id": chunk["chunk_id"],
                "content": chunk["content"],
                "type": chunk.get("metadata", {}).get("type", "unknown")
            }
        })
        new_ids.add(vector_id)

    print(f"✅ Created {len(vectors)} new embeddings (skipped {len(chunks) - len(vectors)})")
    return vectors, new_ids


def upload_to_pinecone(vectors, index, batch_size=100):
    """Upload vectors to Pinecone in batches."""
    if not vectors:
        print("⚠️ No new vectors to upload.")
        return False

    print(f"📤 Uploading {len(vectors)} vectors to Pinecone...")
    for i in tqdm(range(0, len(vectors), batch_size), desc="Uploading"):
        batch = vectors[i:i + batch_size]
        index.upsert(vectors=batch)
        time.sleep(0.1)  # avoid rate limits
    print("✅ Upload complete!")
    return True


if __name__ == "__main__":
    # Initialize Pinecone
    index = initialize_pinecone()
    if not index:
        exit(1)

    # Load uploaded IDs
    uploaded_ids = load_uploaded_ids()

    # Example: your chunks loaded from URLs/docs
    # chunks = load_your_chunks_somehow()
    chunks = []  # replace with your actual chunks

    # Create embeddings only for new chunks
    vectors, new_ids = create_embeddings(chunks, uploaded_ids)

    # Upload new vectors
    upload_to_pinecone(vectors, index)

    # Update local ID tracker
    uploaded_ids.update(new_ids)
    save_uploaded_ids(uploaded_ids)
