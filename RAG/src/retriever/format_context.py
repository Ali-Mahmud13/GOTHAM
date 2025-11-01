from typing import List, Dict
from src.config.settings import MAX_CONTEXT_LENGTH


def format_context(retrieved_chunks: List[Dict], include_scores: bool = False) -> str:
    """Format retrieved chunks into a context string with optional relevance scores."""
    if not retrieved_chunks:
        return "No relevant context found."
    
    context_parts = []
    current_length = 0
    
    # Sort by score (highest first) to include most relevant chunks first
    sorted_chunks = sorted(retrieved_chunks, key=lambda x: x['score'], reverse=True)
    
    for chunk in sorted_chunks:
        # Include score if requested
        score_str = f" [Relevance: {chunk['score']:.3f}]" if include_scores else ""
        chunk_text = f"From {chunk['source']}{score_str}:\n{chunk['content']}\n\n"
        chunk_length = len(chunk_text)
        
        # Check if adding this chunk would exceed max context length
        if current_length + chunk_length > MAX_CONTEXT_LENGTH:
            remaining_space = MAX_CONTEXT_LENGTH - current_length
            if remaining_space > 100:  # Only truncate if we have meaningful space left
                # Truncate at word boundary
                truncated_content = ' '.join(chunk['content'][:remaining_space-50].split()[:-1])
                truncated_chunk = f"From {chunk['source']}{score_str}:\n{truncated_content}...\n\n"
                context_parts.append(truncated_chunk)
            break
        
        context_parts.append(chunk_text)
        current_length += chunk_length
    
    if not context_parts:
        return "No relevant context could be formatted within length constraints."
    
    return "".join(context_parts).strip()


def create_medical_prompt(question: str, context: str) -> str:
    """Create a specialized prompt for medical questions."""
    
    prompt = f"""You are a medical assistant analyzing clinical documents. Based on the provided medical context, please answer the question accurately and professionally.

Important guidelines:
- Base your answer ONLY on the provided context
- Be precise and factual
- If context is insufficient, clearly state what information is missing
- Use medical terminology appropriately
- Do not make assumptions beyond the provided context

Medical Context:
{context}

Clinical Question: {question}

Professional Analysis:"""
    
    return prompt


def format_context_with_scores(retrieved_chunks: List[Dict]) -> str:
    """Format context with relevance scores for debugging."""
    return format_context(retrieved_chunks, include_scores=True)

def estimate_token_count(text: str) -> int:
    """Roughly estimate token count (approx 4 chars per token)."""
    return len(text) // 4


def validate_context_length(context: str, max_tokens: int = None) -> bool:
    """Check if context is within acceptable length."""
    if max_tokens is None:
        max_tokens = MAX_CONTEXT_LENGTH // 4  # Convert chars to approx tokens
    
    token_count = estimate_token_count(context)
    return token_count <= max_tokens


