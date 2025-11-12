import logging
from src.config.settings import PINECONE_INDEX_NAME
from src.ingest.load_urls import load_multiple_urls
from src.ingest.preprocess import preprocess_documents
from src.ingest.embed_upload import create_embeddings, upload_to_pinecone
from src.retriever.query_pinecone import retrieve_similar_chunks, index_exists_and_populated
from src.retriever.format_context import format_context, create_prompt
from src.generator.answer_llm import AnswerGenerator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

class TestRAG:
    def __init__(self):
        self.generator = AnswerGenerator()
        self.urls = ["https://pmc.ncbi.nlm.nih.gov/articles/PMC11657143/"]

    def setup_knowledge_base(self):
        """Load, preprocess, embed, and upload documents if not already in Pinecone."""
        logging.info("Checking if knowledge base already exists...")

        if index_exists_and_populated(PINECONE_INDEX_NAME):
            logging.info("Knowledge base already exists. Skipping ingestion.")
            return True

        logging.info("Loading document from URL...")
        documents = load_multiple_urls(self.urls)
        if not documents:
            logging.warning("❌ Failed to load document.")
            return False

        logging.info(f"✅ Loaded {len(documents)} document(s)")
        chunks = preprocess_documents(documents)
        if not chunks:
            logging.warning("❌ No chunks created from documents.")
            return False

        logging.info("Creating embeddings...")
        vectors = create_embeddings(chunks)

        logging.info("Uploading embeddings to Pinecone...")
        upload_to_pinecone(vectors)

        logging.info("✅ Knowledge base setup completed!")
        return True

    def ask_question(self, question: str, top_k: int = 3):
        logging.info(f"🔍 Searching for answer to: '{question}'")
        chunks = retrieve_similar_chunks(question, top_k=top_k)

        if not chunks:
            logging.warning("❌ No relevant chunks found.")
            return

        logging.info(f"📚 Found {len(chunks)} relevant chunks")
        context = format_context(chunks)
        prompt = create_prompt(question, context)

        logging.info("🤖 Generating answer...")
        answer = self.generator.generate_answer(prompt)

        print("\n" + "="*60)
        print("💡 ANSWER:")
        print("="*60)
        print(answer)
        print("\n" + "="*60)

        print("\n📖 SOURCES:")
        for i, chunk in enumerate(chunks, 1):
            print(f"{i}. {chunk['source']} (score: {chunk['score']:.3f})")


def main():
    logging.info("🚀 Running RAG test for a single document")
    rag = TestRAG()

    if not rag.setup_knowledge_base():
        logging.error("Failed to set up knowledge base.")
        return

    test_question = "What is the study about in this document?"
    rag.ask_question(test_question)


if __name__ == "__main__":
    main()
