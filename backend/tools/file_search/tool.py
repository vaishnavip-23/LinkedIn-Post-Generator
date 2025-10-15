"""
File Search Tool - Main agent tool for document analysis

Searches uploaded documents and retrieves relevant content
based on user's topic query.
"""

from agents import function_tool

from backend.tools.file_search.rag import retrieve_chunks

# Document storage (set by main.py)
document_store = None


def set_document_store(store):
    """Set document storage reference from main.py."""
    global document_store
    document_store = store


@function_tool
async def file_search(file_id: str, topic_query: str) -> str:
    """Search uploaded document for content about a specific topic.

    Use this when user has uploaded a PDF and wants to create a LinkedIn
    post about a specific topic from that document.

    Args:
        file_id: Document ID from upload
        topic_query: User's specific topic or angle

    Returns:
        Relevant document content (full text or retrieved chunks)
    """
    if not document_store or file_id not in document_store:
        raise ValueError("Document not found. Please upload a document first.")

    doc = document_store[file_id]

    # Tier 1: Direct extraction (≤80k tokens)
    if doc.tier == "direct":
        return f"""Document: {doc.filename}
Topic: {topic_query}

Full document content:
{doc.full_text}

Create a LinkedIn post focusing on: {topic_query}"""

    # Tier 2: RAG retrieval (>80k tokens)
    relevant_content = retrieve_chunks(
        file_id=doc.vector_store_id,
        user_query=topic_query
    )

    return f"""Document: {doc.filename} ({doc.token_count:,} tokens)
Topic: {topic_query}

Relevant sections retrieved using semantic search:
{relevant_content}

Create a LinkedIn post focusing on: {topic_query}"""
