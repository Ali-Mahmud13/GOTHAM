from sentence_transformers import SentenceTransformer
from typing import List, Dict
from src.utils.pinecone_client import index, index_exists_and_populated  # ✅ use shared client
from src.config.settings import EMBEDDING_MODEL
from src.config.settings import DIMENSION



def retrieve_similar_chunks(question: str, top_k: int = 5) -> List[Dict]:
    """Retrieve similar chunks from Pinecone based on question."""
    try:
        print(f"🔍 Searching for similar chunks...")
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

        # Extract useful fields from retrieved matches
        retrieved_chunks = [
            {
                'content': match.metadata.get('content', ''),
                'source': match.metadata.get('source', ''),
                'score': match.score, # similarity score
                'chunk_id': match.metadata.get('chunk_id', 0),
                'type': match.metadata.get('type', 'unknown'),
            }
            for match in results.matches
        ]

        # Sort by descending similarity score (best match first)
        retrieved_chunks.sort(key=lambda x: x['score'], reverse=True)
        print(f"✅ Retrieved {len(retrieved_chunks)} chunks (best score: {retrieved_chunks[0]['score']:.3f})")
        return retrieved_chunks

    except Exception as e:
        print(f"❌ Error retrieving chunks: {e}")
        return []


def get_all_urls_from_pinecone() -> list:
    """
    Return a list of all document URLs stored in Pinecone metadata.
    Fixed to handle vector_count properly.
    """
    urls = set()  # use set to avoid duplicates
    try:
        stats = index.describe_index_stats()
        namespaces = stats.get('namespaces', {})

        for ns in namespaces.keys():
            # You cannot iterate over vector_count because it's an int
            # Instead, fetch vectors using the namespace
            # We'll fetch in batches (e.g., 1000 at a time)
            vector_count = namespaces[ns].get('vector_count', 0)
            if vector_count == 0:
                continue

            # Get all IDs in this namespace (you might need to store IDs elsewhere if Pinecone doesn't provide fetch-all)
            # For simplicity, assume we fetch using a match_all query
            query_results = index.query(
                vector=[0]*DIMENSION,  # dummy vector, won't affect metadata-only retrieval
                top_k=vector_count,
                include_metadata=True,
                namespace=ns
            )

            for match in getattr(query_results, "matches", []):
                meta = match.metadata or {}
                if 'source' in meta:
                    urls.add(meta['source'])

    except Exception as e:
        print(f"❌ Error fetching URLs: {e}")

    return list(urls)



def test_retrieval():
    print("Testing Pinecone retrieval...")
    question = "medical guidelines"
    chunks = retrieve_similar_chunks(question, top_k=2)
    if chunks:
        print(f"✅ Retrieved {len(chunks)} chunks")
    else:
        print("❌ No chunks retrieved")
