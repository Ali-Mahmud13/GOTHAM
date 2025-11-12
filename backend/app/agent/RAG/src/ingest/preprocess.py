from typing import List, Dict
import re
from src.config.settings import CHUNK_SIZE, CHUNK_OVERLAP

def split_text_into_chunks(
    text: str, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP
) -> List[str]:
    """Split text into overlapping chunks based on words."""
    words = text.split()
    if not words:
        return []
    
    chunks = []
    i = 0
    while i < len(words):
        chunk_words = words[i:i + chunk_size]
        chunks.append(' '.join(chunk_words))
        # Move window forward, ensuring overlap
        step = chunk_size - chunk_overlap
        i += step if step > 0 else chunk_size
    return chunks

def split_markdown_by_headings(markdown_content: str) -> List[Dict[str, str]]:
    """Splits Markdown content into chunks based on headings."""
    # Regex to find headings (e.g., #, ##, ###)
    # This will split the text by headings, keeping the headings with the content that follows.
    # The regex looks for a newline followed by one or more '#' characters and a space.
    # It uses a positive lookahead `(?=...)` to split without removing the delimiter.
    sections = re.split(r'(?=\n#{1,6}\s)', markdown_content)
    
    chunks = []
    for i, section in enumerate(sections):
        if section.strip():
            # The first part might not have a heading, so we give it a generic one.
            heading_match = re.match(r'^(#{1,6}\s.*)', section.strip())
            heading = heading_match.group(1).strip() if heading_match else f"Section {i+1}"
            
            chunks.append({
                "heading": heading,
                "content": section.strip()
            })
    return chunks

def preprocess_documents(documents: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Preprocess and chunk all input documents based on their type."""
    processed_chunks = []

    for doc in documents:
        text = doc.get('content', '').strip()
        doc_type = doc.get('type', 'unknown')
        source = doc.get('source', 'unknown')
        
        if not text:
            continue

        chunks = []
        if doc_type == 'markdown':
            # For markdown, we first split by headings, then chunk the text within each section
            md_sections = split_markdown_by_headings(text)
            for section in md_sections:
                section_text = section['content']
                sub_chunks = split_text_into_chunks(section_text)
                for i, sub_chunk in enumerate(sub_chunks):
                    processed_chunks.append({
                        'source': source,
                        'chunk_id': len(processed_chunks),
                        'content': sub_chunk,
                        'metadata': {
                            'source': source,
                            'type': doc_type,
                            'heading': section['heading'],
                            'chunk_id_in_section': i,
                        }
                    })
            continue # Move to the next document

        else:
            # For other document types, use the standard text chunker
            chunks = split_text_into_chunks(text)

        # Create structured chunk entries for non-markdown docs
        for i, chunk_content in enumerate(chunks):
            processed_chunks.append({
                'source': source,
                'chunk_id': len(processed_chunks),
                'content': chunk_content,
                'metadata': {
                    'source': source,
                    'type': doc_type,
                    'chunk_id': i,
                    'total_chunks': len(chunks)
                }
            })

    print(f"✅ Created {len(processed_chunks)} chunks from {len(documents)} documents")
    return processed_chunks