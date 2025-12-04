import requests
from typing import List, Dict, Optional
import fitz  # PyMuPDF
from bs4 import BeautifulSoup
import time
import re
import os

def load_url_content(url: str) -> Optional[Dict[str, str]]:
    """Load content from a URL (supporting HTML, PDF, and Markdown)."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        content_type = response.headers.get('content-type', '').lower()
        
        if 'pdf' in content_type or url.lower().endswith('.pdf'):
            return load_pdf_from_bytes(url, response.content)
        elif 'markdown' in content_type or url.lower().endswith('.md'):
            return load_markdown_content(url, response.text)
        else:
            return load_html_content(url, response.text)
        
    except requests.RequestException as e:
        print(f"⚠️ Error loading {url}: {e}")
        return None

def load_pdf_from_bytes(source: str, pdf_data: bytes) -> Optional[Dict[str, str]]:
    """Extract text from in-memory PDF bytes."""
    try:
        with fitz.open(stream=pdf_data, filetype="pdf") as doc:
            text = "".join(page.get_text("text", flags=0) for page in doc)
            return {
                "source": source,
                "content": text.strip(),
                "type": "pdf",
            }
    except Exception as e:
        print(f"⚠️ Error parsing PDF from {source}: {e}")
        return None

def load_html_content(url: str, html_content: str) -> Optional[Dict[str, str]]:
    """Extract clean text from HTML."""
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        for element in soup(["script", "style", "header", "footer", "nav", "aside"]):
            element.decompose()
        text = " ".join(soup.get_text(separator=" ", strip=True).split())
        return {"source": url, "content": text, "type": "webpage"}
    except Exception as e:
        print(f"⚠️ Error processing HTML from {url}: {e}")
        return None

def load_markdown_content(source: str, markdown_content: str) -> Optional[Dict[str, str]]:
    """Load content from a Markdown string."""
    try:
        # Simple conversion: just use the text content. More advanced parsing can be added.
        return {
            "source": source,
            "content": markdown_content.strip(),
            "type": "markdown",
        }
    except Exception as e:
        print(f"⚠️ Error processing Markdown from {source}: {e}")
        return None

def load_local_file(file_path: str) -> Optional[Dict[str, str]]:
    """Load content from a local file (PDF or Markdown)."""
    try:
        if not os.path.exists(file_path):
            print(f"⚠️ File not found: {file_path}")
            return None

        file_ext = os.path.splitext(file_path)[1].lower()
        with open(file_path, 'rb') as f:
            if file_ext == '.pdf':
                return load_pdf_from_bytes(file_path, f.read())
            elif file_ext == '.md':
                return load_markdown_content(file_path, f.read().decode('utf-8'))
            else:
                print(f"⚠️ Unsupported file type: {file_path}")
                return None
    except Exception as e:
        print(f"⚠️ Error loading local file {file_path}: {e}")
        return None

def load_multiple_sources(urls: List[str] = [], files: List[str] = [], delay: int = 1) -> List[Dict[str, str]]:
    """Load content from multiple URLs and local files with rate limiting."""
    documents = []

    # Load from URLs
    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] 🌐 Loading URL: {url}")
        doc = load_url_content(url)
        if doc and doc["content"]:
            print(f"✅ Successfully loaded URL: {url} ({len(doc['content'])} chars)")
            documents.append(doc)
        else:
            print(f"❌ Failed to load URL: {url}")
        time.sleep(delay)

    # Load from local files
    for i, file_path in enumerate(files, 1):
        print(f"\n[{i}/{len(files)}] 📄 Loading file: {file_path}")
        doc = load_local_file(file_path)
        if doc and doc["content"]:
            print(f"✅ Successfully loaded file: {file_path} ({len(doc['content'])} chars)")
            documents.append(doc)
        else:
            print(f"❌ Failed to load file: {file_path}")

    print(f"\n📄 Total documents loaded: {len(documents)}")
    return documents