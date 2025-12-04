import os
import warnings
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
warnings.filterwarnings("ignore")

import logging
from typing import List, Dict
from src.ingest.load_urls import load_multiple_sources
from src.ingest.preprocess import preprocess_documents
from src.ingest.embed_upload import create_embeddings, upload_to_pinecone
from src.retriever.query_pinecone import retrieve_similar_chunks, get_all_sources_from_pinecone
from src.utils.local_ids import load_uploaded_ids, save_uploaded_ids
from src.utils.pinecone_client import initialize_pinecone, index  # Import shared client

logging.basicConfig(level=logging.ERROR, format="%(asctime)s | %(levelname)s | %(message)s")

class SimpleRetriever:
    """
    Orchestrates loading documents, embedding them, storing in Pinecone, and retrieving relevant chunks.
    """
    def __init__(self):
        # Documents to be loaded from web URLs
        self.urls = [
            "https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0044129",
            "https://perigen.com/wp-content/uploads/2017/05/2014-BJM-Meows.pdf",
            "https://pmc.ncbi.nlm.nih.gov/articles/PMC11657143/",
            "https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0179332"
        ]
        self.files = [
            # "path/to/your/document.pdf",
            # "path/to/your/notes.md"
        ]
        initialize_pinecone() # Ensure Pinecone is ready

    def setup_knowledge_base(self):
        """
        Checks for new documents, processes them, and uploads their embeddings to Pinecone.
        It avoids re-processing existing documents.
        """
        logging.info("🛠️ Setting up the knowledge base...")
        
        try:
            # Get sources already in Pinecone and locally tracked IDs
            existing_sources = set(get_all_sources_from_pinecone())
            uploaded_ids = load_uploaded_ids()
            
            # Determine which sources are new
            new_urls = [url for url in self.urls if url not in existing_sources]
            new_files = [file for file in self.files if file not in existing_sources]

            if not new_urls and not new_files:
                logging.info("✅ Knowledge base is already up-to-date.")
                return True

            logging.info(f"Found {len(new_urls)} new URLs and {len(new_files)} new files to process.")
            
            # Load, preprocess, and embed new documents
            documents = load_multiple_sources(urls=new_urls, files=new_files)
            if not documents:
                return False

            processed_chunks = preprocess_documents(documents)
            vectors, new_ids = create_embeddings(processed_chunks, uploaded_ids)

            if not vectors:
                logging.info("No new unique chunks to upload.")
                return True

            upload_to_pinecone(vectors)

            # Update and save the list of uploaded IDs
            uploaded_ids.update(new_ids)
            save_uploaded_ids(uploaded_ids)
            
            logging.info("✅ Knowledge base setup complete!")
            return True

        except Exception as e:
            logging.error(f"❌ An error occurred during knowledge base setup: {e}")
            return False

