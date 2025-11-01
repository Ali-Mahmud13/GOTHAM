import requests
from typing import List, Dict, Optional
import fitz #PyMuPDF
from bs4 import BeautifulSoup
import time

def load_url_content(url: str) -> Optional[Dict[str, str]]:
    # Load content from a url (supporting HTML and PDF)
    try:
        headers = {
            # Use headers to mimic a real browser request
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status() # Raises error for 4xx/5xx responses

        content_type = response.headers.get('content-type', '').lower()

        if 'pdf' in content_type or url.lower().endswith('.pdf'):
            # If PDF, send raw bytes to PDF extraction function
            return load_pdf_from_bytes(url, response.content)
        else:
            # Otherwise, treat it as a normal web page
            return load_html_content(url, response.text)
        
    except Exception as e:
        print(f"⚠️ Error loading {url}: {e}")
        return None
    
def load_pdf_from_bytes(url: str, pdf_data: bytes) -> Optional[Dict[str, str]]:
    """Extract text from in-memory PDF bytes."""
    try:
        with fitz.open(stream=pdf_data, filetype="pdf") as doc:
            text = ""
            
            # Loop through pages and extract text
            for page in doc:
                text += page.get_text("text", flags=0)

            return {
                "source": url,
                "content": text.strip(), # extracted text content
                "type": "pdf",
                "pages": len(doc), # no of pages extracted
            }

    except Exception as e:
        print(f"⚠️ Error parsing PDF from {url}: {e}")
        return None


def load_html_content(url: str, html_content: str) -> Optional[Dict[str, str]]:
    """Extract clean text from HTML."""
    try:
        soup = BeautifulSoup(html_content, "html.parser")

        # Remove scripts, styles, and nav elements
        for element in soup(["script", "style", "header", "footer", "nav", "aside"]):
            element.decompose()

        # Extract visible text
        text = soup.get_text(separator=" ", strip=True)

        # Clean multiple spaces/newlines with single spaces
        text = " ".join(text.split())

        return {
            "source": url,
            "content": text,
            "type": "webpage", # marked as a webpage
        }

    except Exception as e:
        print(f"⚠️ Error processing HTML from {url}: {e}")
        return None


def load_multiple_urls(urls: List[str], delay: int = 2) -> List[Dict[str, str]]:
    """Load content from multiple URLs with rate limiting."""
    documents = []

    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] 🌐 Loading: {url}")
        doc = load_url_content(url)

        if doc and doc["content"]:
            print(f"✅ Successfully loaded: {url} ({len(doc['content'])} chars)")
            documents.append(doc)
        else:
            print(f"❌ Failed to load: {url}")

        # small delay between requests
        time.sleep(delay)

    print(f"\n📄 Total documents loaded: {len(documents)} / {len(urls)}")
    return documents