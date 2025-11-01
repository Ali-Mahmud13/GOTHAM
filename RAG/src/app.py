import logging
from src.config.settings import PINECONE_INDEX_NAME
from src.ingest.load_urls import load_multiple_urls
from src.ingest.preprocess import preprocess_documents
from src.ingest.embed_upload import create_embeddings, upload_to_pinecone, initialize_pinecone
from src.retriever.query_pinecone import retrieve_similar_chunks, index_exists_and_populated, get_all_urls_from_pinecone
from src.retriever.format_context import format_context, create_medical_prompt
from src.generator.answer_llm import AnswerGenerator
from src.utils.local_ids import load_uploaded_ids, save_uploaded_ids  # For tracking uploaded chunk IDs locally

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

class SimpleRAG:
    # Loads document -> converts to embeddings -> stores in Pinecone -> retrieves chunks -> uses LLM for answer

    def __init__(self):
        self.generator = AnswerGenerator()
        self.urls = [
            "https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0044129",
            "https://perigen.com/wp-content/uploads/2017/05/2014-BJM-Meows.pdf",
            "https://pmc.ncbi.nlm.nih.gov/articles/PMC11657143/",
            "https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0179332"
        ]

        # prevents reuploading the same vectors
        self.local_ids = load_uploaded_ids()  # e.g., {'chunk_ids': []}

    def setup_knowledge_base(self):
        logging.info("Checking if knowledge base already exists...")

        # Initialize Pinecone
        pinecone_index = initialize_pinecone()
        if not pinecone_index:
            logging.error("Failed to initialize Pinecone index.")
            return False

        # Load existing uploaded vector IDs
        existing_ids = load_uploaded_ids().get("chunk_ids", set())

        # Check existing URLs in Pinecone
        existing_urls = set()
        if index_exists_and_populated(PINECONE_INDEX_NAME):
            logging.info("Knowledge base exists. Checking for new documents to add...")
            try:
                existing_urls = set(get_all_urls_from_pinecone())
            except Exception as e:
                logging.warning(f"Could not fetch existing URLs from Pinecone: {e}")

        # Only load new URLs
        new_urls = [url for url in self.urls if url not in existing_urls]
        if not new_urls:
            logging.info("No new documents to add. Knowledge base is up-to-date.")
            return True

        logging.info(f"Loading documents from {len(new_urls)} new URL(s)...")
        try:
            documents = load_multiple_urls(new_urls)
        except Exception as e:
            logging.error(f"Error loading URLs: {e}")
            return False

        if not documents:
            logging.warning("No documents were successfully loaded.")
            return False

        logging.info(f"Successfully loaded {len(documents)} new document(s)")

        # Preprocess and chunk
        processed_chunks = preprocess_documents(documents)
        if not processed_chunks:
            logging.warning("No chunks created from documents.")
            return False

        # Create embeddings only for new chunks (skip already uploaded)
        vectors, new_ids = create_embeddings(processed_chunks, existing_ids)
        if not vectors:
            logging.info("All chunks already uploaded. Skipping embedding.")
            return True

        logging.info(f"Uploading {len(vectors)} new vectors to Pinecone...")
        try:
            upload_to_pinecone(vectors, index=pinecone_index)
        except Exception as e:
            logging.error(f"Error uploading to Pinecone: {e}")
            return False

        # Update local_ids to include newly uploaded vector IDs
        chunk_ids = set(self.local_ids.get("chunk_ids", []))
        chunk_ids.update(new_ids)
        self.local_ids["chunk_ids"] = list(chunk_ids)
        save_uploaded_ids(self.local_ids)

        logging.info("✅ Knowledge base setup completed with new documents!")
        return True

    def ask_question(self, question: str, top_k: int = 3):
        logging.info(f"🔍 Searching for answer: '{question}'")

        chunks = retrieve_similar_chunks(question, top_k=top_k)
        if not chunks:
            logging.warning("❌ No relevant information found.")
            return

        logging.info(f"📚 Found {len(chunks)} relevant sections")

        context = format_context(chunks)
        prompt = create_medical_prompt(question, context)

        logging.info("🤖 Generating answer...")
        answer = self.generator.generate_answer(prompt)

        # Display results
        print("\n" + "=" * 60)
        print("💡 ANSWER:")
        print("=" * 60)
        print(answer)
        print("\n" + "=" * 60)

        # Show sources
        print("\n📖 Sources:")
        for i, chunk in enumerate(chunks, 1):
            print(f"{i}. {chunk['source']} (score: {chunk['score']:.3f})")


def main():
    logging.info("🚀 Welcome to Simple RAG System!")
    logging.info("This system processes medical documents from URLs and answers questions.")

    rag = SimpleRAG()

    # Set up the knowledge base
    logging.info("Setting up knowledge base...")
    success = rag.setup_knowledge_base()
    if not success:
        logging.error("Failed to set up knowledge base. Please check URLs and internet connection.")
        return

    # Q&A loop
    logging.info("Ready to ask questions! Type 'quit' to exit.")
    while True:
        question = input("\n❓ Enter your question: ").strip()
        if question.lower() in ['quit', 'exit', 'q']:
            logging.info("👋 Goodbye!")
            break
        if question:
            rag.ask_question(question)


if __name__ == "__main__":
    main()
