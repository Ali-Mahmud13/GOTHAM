from typing import List, Dict
from src.config.settings import CHUNK_SIZE, CHUNK_OVERLAP

def split_text_into_chunks(
    text: str, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP
) -> List[str]:
    """Split text into overlapping chunks."""

    # split into individual words
    words = text.split()
    chunks = []

    i = 0
    # moving window over the words list
    while i < len(words):
        chunk_words = words[i:i + chunk_size]
        # words converted back to chunk
        chunk = ' '.join(chunk_words)
        chunks.append(chunk)
        i += chunk_size - chunk_overlap  # move the window

    return chunks


def preprocess_documents(documents: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Preprocess and chunk all input documents."""
    processed_chunks = []

    for doc in documents:
        text = doc.get('content', '').strip()
        if not text:
            continue

        # Basic cleanup: remove extra spaces and line breaks
        text = ' '.join(text.split())

        # Split into chunks
        chunks = split_text_into_chunks(text)

        # Create structured chunk entries
        for i, chunk in enumerate(chunks):
            processed_chunks.append({
                'source': doc.get('source', 'unknown'),
                'chunk_id': i, # index of this chunk
                'content': chunk,
                'metadata': {
                    'source': doc.get('source', 'unknown'),
                    'type': doc.get('type', 'unknown'),
                    'chunk_id': i,
                    'total_chunks': len(chunks) # total chunks from same doc
                }
            })

    print(f"✅ Created {len(processed_chunks)} chunks from {len(documents)} documents")
    return processed_chunks
