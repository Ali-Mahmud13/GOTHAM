from sentence_transformers import SentenceTransformer
from typing import List, Dict
from src.utils.pinecone_client import index, index_exists_and_populated
from src.config.settings import EMBEDDING_MODEL, DIMENSION

def retrieve_similar_chunks(question: str, top_k: int = 5) -> List[Dict]:
    """Retrieve similar chunks from Pinecone based on question."""
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
            include_metadata=True
        )

        if not results or not getattr(results, "matches", []):
            print("❌ No relevant chunks found in Pinecone.")
            return []

        retrieved_chunks = [
            {
                'content': match.metadata.get('content', ''),
                'source': match.metadata.get('source', ''),
                'score': match.score,
                'heading': match.metadata.get('heading', None), # For Markdown
                'chunk_id': match.metadata.get('chunk_id', 0),
                'type': match.metadata.get('type', 'unknown'),
            }
            for match in results.matches
        ]

        retrieved_chunks.sort(key=lambda x: x['score'], reverse=True)
        print(f"✅ Retrieved {len(retrieved_chunks)} chunks (best score: {retrieved_chunks[0]['score']:.3f})")
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
        # Fetch all vector IDs to then fetch their metadata
        # This is a simplified approach. For very large indexes, a different strategy may be needed.
        # Here we query with a dummy vector to get all items.
        # This might be slow and memory-intensive for millions of vectors.
        vector_count = stats.get('total_vector_count', 0)
        if vector_count == 0:
            return []

        # A more robust way would be to paginate through all vectors, but that's complex.
        # This query will be capped by Pinecone's top_k limit (e.g., 10,000).
        # For this project's scale, it should be sufficient.
        all_vectors = index.query(
            vector=[0] * DIMENSION, # Dummy vector
            top_k=min(vector_count, 10000), # Respect Pinecone's limit
            include_metadata=True,
        )
        
        for match in all_vectors.get('matches', []):
            if 'source' in match.metadata:
                sources.add(match.metadata['source'])

    except Exception as e:
        print(f"❌ Error fetching all sources from Pinecone: {e}")

    return list(sources)