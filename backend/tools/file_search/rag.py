"""
RAG Pipeline - Semantic search with multi-query expansion

Handles chunking, embedding, and retrieval using ChromaDB.
"""

import os
from typing import List
from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions
from openai import OpenAI
import instructor

from backend.models.schema import QueryExpansion
from backend.tools.file_search.config import (
    EMBEDDING_MODEL,
    LLM_MODEL,
    CHUNK_SIZE_TOKENS,
    CHUNK_OVERLAP_TOKENS,
    TOP_K_CHUNKS
)

# Load environment variables
load_dotenv()

# Set ChromaDB API key
os.environ["CHROMA_OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")

# Initialize ChromaDB (in-memory for session storage)
chroma_client = chromadb.Client()

# Initialize OpenAI embedding function
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    model_name=EMBEDDING_MODEL
)

# Initialize Instructor client for query expansion
instructor_client = instructor.from_openai(
    OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
)


def chunk_text(text: str) -> List[str]:
    """Split text into overlapping chunks.

    Args:
        text: Full document text

    Returns:
        List of text chunks
    """
    # Convert token counts to approximate word counts
    words = text.split()
    words_per_chunk = int(CHUNK_SIZE_TOKENS * 0.75)
    overlap_words = int(CHUNK_OVERLAP_TOKENS * 0.75)

    chunks = []
    start = 0

    while start < len(words):
        end = start + words_per_chunk
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start = end - overlap_words

    return chunks


def create_vector_store(file_id: str, text: str) -> str:
    """Create vector store and embed document chunks.

    Args:
        file_id: Unique document identifier
        text: Full document text

    Returns:
        Collection ID (same as file_id)
    """
    # Split into chunks
    chunks = chunk_text(text)

    # Create ChromaDB collection
    collection = chroma_client.create_collection(
        name=file_id,
        embedding_function=openai_ef
    )

    # Add chunks with metadata
    ids = [f"{file_id}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"chunk_index": i} for i in range(len(chunks))]

    collection.add(
        documents=chunks,
        ids=ids,
        metadatas=metadatas
    )

    return file_id


def expand_query(user_query: str) -> List[str]:
    """Expand query into semantic variations using LLM.

    Args:
        user_query: Original user query

    Returns:
        List including original + 3-5 variations
    """
    prompt = f"""Generate 3-5 semantic variations of this query for better document retrieval:

Query: "{user_query}"

Create variations that rephrase the concept using different words while keeping the core intent."""

    result = instructor_client.chat.completions.create(
        model=LLM_MODEL,
        response_model=QueryExpansion,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    # Combine original with variations
    return [user_query] + result.expanded_queries


def retrieve_chunks(file_id: str, user_query: str) -> str:
    """Retrieve relevant chunks using multi-query expansion.

    Args:
        file_id: Document collection ID
        user_query: User's topic query

    Returns:
        Combined relevant chunks as text
    """
    # Get collection
    collection = chroma_client.get_collection(
        name=file_id,
        embedding_function=openai_ef
    )

    # Expand query
    queries = expand_query(user_query)

    # Retrieve chunks for each query variation
    seen_chunks = {}

    for query in queries:
        results = collection.query(
            query_texts=[query],
            n_results=TOP_K_CHUNKS
        )

        # Deduplicate and store chunks
        if results["ids"] and results["documents"]:
            for chunk_id, chunk_text in zip(results["ids"][0], results["documents"][0]):
                if chunk_id not in seen_chunks:
                    seen_chunks[chunk_id] = chunk_text

    # Sort by chunk index to maintain document order
    sorted_chunks = sorted(
        seen_chunks.items(),
        key=lambda x: int(x[0].split("_chunk_")[1])
    )

    # Combine into single text
    return "\n\n".join([chunk for _, chunk in sorted_chunks])


def delete_vector_store(file_id: str) -> None:
    """Delete ChromaDB collection.

    Args:
        file_id: Document collection ID
    """
    try:
        chroma_client.delete_collection(name=file_id)
    except Exception:
        pass  # Already deleted or doesn't exist
