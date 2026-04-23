# backend/app/agent/RAG/src/retriever/query_pinecone.py
import sys
from pathlib import Path

# Add project root to path FIRST - before any local imports
project_root = Path(__file__).resolve().parents[6]  # 6 levels up to GOTHAM/
sys.path.insert(0, str(project_root))

# Now do your imports
from typing import List, Dict
from app.agent.RAG.src.utils.pinecone_client import index, index_exists_and_populated
from config import EMBEDDING_MODEL, DIMENSION

def retrieve_similar_chunks(question: str, top_k: int = 5) -> List[str]:
    """Retrieve similar chunks from Pinecone based on question. Returns only content."""
    try:
        from sentence_transformers import SentenceTransformer
    except (ImportError, ValueError, RuntimeError) as e:
        # Handle TensorFlow/Keras import errors
        error_msg = str(e)
        if any(kw in error_msg for kw in ['tf_keras', 'Keras', 'TensorFlow']):
            print(f"⚠️ Warning: Could not load sentence_transformers due to TensorFlow issue: {error_msg}")
            print("⚠️ Falling back to empty retrieval (embeddings unavailable)")
            return []
        raise

    if not index_exists_and_populated():
        print("⚠️ Cannot retrieve chunks, Pinecone index is not ready or is empty.")
        return []

    try:
        print(f"🧠 Embedding query and searching for top {top_k} similar chunks...")
        model = SentenceTransformer(EMBEDDING_MODEL)
        question_embedding = model.encode(question, normalize_embeddings=True).tolist()

        results = index.query(
            vector=question_embedding,
            top_k=top_k,
            include_metadata=True  # Need metadata to get the content
        )

        if not results or not getattr(results, "matches", []):
            print("❌ No relevant chunks found in Pinecone.")
            return []

        # Extract only the content from metadata
        retrieved_chunks = [
            match.metadata.get('content', '') 
            for match in results.matches 
            if match.metadata.get('content')
        ]

        print(f"✅ Retrieved {len(retrieved_chunks)} chunks")
        return retrieved_chunks

    except Exception as e:
        print(f"❌ Error retrieving chunks: {e}")
        return []

def get_all_sources_from_pinecone() -> List[str]:
    """Return a list of all unique source URLs/paths stored in Pinecone."""
    sources = set()
    if not index_exists_and_populated():
        return []
        
    try:
        stats = index.describe_index_stats()
        vector_count = stats.get('total_vector_count', 0)
        if vector_count == 0:
            return []

        all_vectors = index.query(
            vector=[0] * DIMENSION,
            top_k=min(vector_count, 10000),
            include_metadata=True,
        )
        
        for match in all_vectors.get('matches', []):
            if 'source' in match.metadata:
                sources.add(match.metadata['source'])

    except Exception as e:
        print(f"❌ Error fetching all sources from Pinecone: {e}")

    return list(sources)