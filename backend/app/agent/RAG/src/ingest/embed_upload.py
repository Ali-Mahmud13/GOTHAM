import time
from tqdm import tqdm
from pinecone import Pinecone
from src.config.settings import EMBEDDING_MODEL
from src.utils.pinecone_client import index  # Use the shared client

def create_embeddings(chunks, existing_ids):
    """Create embeddings only for new chunks."""
    # Lazy import to avoid TensorFlow initialization
    from sentence_transformers import SentenceTransformer

    print("🧠 Loading embedding model...")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print(f"✅ Loaded model: {EMBEDDING_MODEL}")

    vectors = []
    new_ids = set()

    for chunk in tqdm(chunks, desc="Creating embeddings"):
        # Create a unique ID for each chunk based on source and chunk index
        vector_id = f"{chunk['source'].replace('/', '_')}_{chunk['chunk_id']}"
        if vector_id in existing_ids:
            continue  # Skip if already uploaded

        try:
            emb = model.encode(chunk["content"], normalize_embeddings=True)
            vectors.append({
                "id": vector_id,
                "values": emb.tolist(),
                "metadata": chunk.get("metadata", {})  # Use the rich metadata from preprocessing
            })
            new_ids.add(vector_id)
        except Exception as e:
            print(f"⚠️ Error encoding chunk {vector_id}: {e}")

    print(f"✅ Created {len(vectors)} new embeddings (skipped {len(chunks) - len(vectors)} already existing)")
    return vectors, new_ids


def upload_to_pinecone(vectors, batch_size=100):
    """Upload vectors to Pinecone in batches using the global index."""
    if not vectors:
        print("⚠️ No new vectors to upload.")
        return False

    print(f"📤 Uploading {len(vectors)} vectors to Pinecone...")
    for i in tqdm(range(0, len(vectors), batch_size), desc="Uploading"):
        batch = vectors[i:i + batch_size]
        try:
            index.upsert(vectors=batch)
        except Exception as e:
            print(f"❌ Error during batch upload: {e}")
            # Optional: Add retry logic here
    
    print("✅ Upload complete!")
    return True