"""
File Search Tool - Document analysis with smart tier detection

Analyzes uploaded PDF documents and retrieves relevant content
based on user's topic query. Uses direct extraction or RAG depending
on document size.
"""

from agents import function_tool

# Import document storage from main (will be set during initialization)
document_store = None


def set_document_store(store):
    """Set the document storage reference from main.py."""
    global document_store
    document_store = store


@function_tool
async def file_search(file_id: str, topic_query: str) -> str:
    """Search uploaded document for content related to a specific topic.
    
    Use this when user has uploaded a document and wants to create a LinkedIn
    post about a specific topic or angle from that document.
    
    Args:
        file_id: The document ID returned from upload
        topic_query: User's specific topic or angle for the LinkedIn post
        
    Returns:
        Relevant content from document (full text or retrieved chunks)
    """
    if not document_store or file_id not in document_store:
        raise ValueError(f"Document not found. Please upload a document first.")
    
    doc = document_store[file_id]
    
    # Tier 1: Direct extraction (≤80k tokens)
    if doc.tier == "direct":
        # Return full document text with context
        return f"""Document: {doc.filename}
Topic: {topic_query}

Full document content:
{doc.full_text}

Create a LinkedIn post focusing on: {topic_query}"""
    
    # Tier 2: RAG retrieval (>80k tokens)
    else:
        from backend.tools.rag_pipeline import retrieve_chunks
        
        # Retrieve relevant chunks using multi-query expansion
        relevant_content = retrieve_chunks(
            file_id=doc.vector_store_id,
            user_query=topic_query,
            top_k=10
        )
        
        return f"""Document: {doc.filename} ({doc.token_count:,} tokens)
Topic: {topic_query}

Relevant sections retrieved using semantic search:
{relevant_content}

Create a LinkedIn post focusing on: {topic_query}"""
