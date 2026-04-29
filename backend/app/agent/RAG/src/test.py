import logging
from retriever.query_pinecone import retrieve_similar_chunks

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

def ask_question(question: str, top_k: int = 5):  # ← Removed 'self'
    logging.info(f"🔍 Searching for answer to: '{question}'")
    chunks = retrieve_similar_chunks(question, top_k=top_k)

    if not chunks:
        logging.warning("❌ No relevant chunks found.")
        return

    logging.info(f"📚 Found {len(chunks)} relevant chunks")
    print("\n--- Retrieved Chunks ---")
    print(chunks)


def main():
    test_question = "what is gestational diabetes?"
    ask_question(test_question)


if __name__ == "__main__":
    main()