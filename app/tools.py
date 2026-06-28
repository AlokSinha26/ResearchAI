# app/tools.py
from langchain_core.tools import tool
from ddgs import DDGS
import httpx
import pypdf
import io

@tool
def web_search(query: str) -> str:
    """Search the web and return top result snippets with URLs."""
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=5))
    return "\n\n".join(f"{r['title']} ({r['href']}): {r['body']}" for r in results)

@tool
def read_pdf(url_or_path: str) -> str:
    """Extract text from a PDF given a URL or local path."""
    if url_or_path.startswith("http"):
        content = httpx.get(url_or_path, timeout=20).content
        reader = pypdf.PdfReader(io.BytesIO(content))
    else:
        reader = pypdf.PdfReader(url_or_path)
    text = "\n".join(page.extract_text() or "" for page in reader.pages[:20])
    return text[:8000]

@tool
def query_memory(topic: str) -> str:
    """Retrieve prior research notes related to a topic, if any exist."""
    from app.memories import search_memory
    return search_memory(topic)