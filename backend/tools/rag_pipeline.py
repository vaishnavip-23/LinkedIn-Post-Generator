"""
RAG Pipeline - ChromaDB + Multi-Query Expansion + Retrieval

Handles document chunking, embedding, storage, and semantic retrieval
with multi-query expansion for better results.
"""

import os
from typing import List, Set
from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions
from openai import OpenAI
import instructor

from backend.models.schema import QueryExpansion

# Load environment variables first
load_dotenv()

# Set ChromaDB environment variable (it looks for CHROMA_OPENAI_API_KEY)
os.environ["CHROMA_OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")

# Initialize ChromaDB client (in-memory for session-based storage)
chroma_client = chromadb.Client()

# Initialize OpenAI embedding function for ChromaDB
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    model_name="text-embedding-3-small"
)

# Initialize Instructor client for query expansion
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
instructor_client = instructor.from_openai(openai_client)


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """Split text into overlapping chunks based on token size.
    
    Args:
        text: Full document text
        chunk_size: Target tokens per chunk
        overlap: Overlapping tokens between chunks
        
    Returns:
        List of text chunks
    """
    # Simple word-based chunking (rough approximation of tokens)
    # 1 token ≈ 0.75 words, so 1000 tokens ≈ 750 words
    words = text.split()
    words_per_chunk = int(chunk_size * 0.75)
    overlap_words = int(overlap * 0.75)
    
    chunks = []
    start = 0
    
    while start < len(words):
        end = start + words_per_chunk
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start = end - overlap_words  # Overlap between chunks
    
    return chunks


def create_vector_store(file_id: str, text: str) -> str:
    """Create ChromaDB collection and store document chunks.
    
    Args:
        file_id: Unique document identifier
        text: Full document text
        
    Returns:
        Collection ID (same as file_id)
    """
    # Chunk the document
    chunks = chunk_text(text)
    
    # Create collection for this document
    collection = chroma_client.create_collection(
        name=file_id,
        embedding_function=openai_ef
    )
    
    # Add chunks to collection with metadata
    ids = [f"{file_id}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"chunk_index": i, "file_id": file_id} for i in range(len(chunks))]
    
    collection.add(
        documents=chunks,
        ids=ids,
        metadatas=metadatas
    )
    
    return file_id


def expand_query(user_query: str) -> List[str]:
    """Expand user query into multiple semantic variations using LLM.
    
    Args:
        user_query: Original user query
        
    Returns:
        List of 3-5 expanded query variations
    """
    expansion_prompt = f"""Given this query about a document, generate 3-5 semantically similar 
variations that would help retrieve relevant content from a vector database.

Original query: "{user_query}"

Generate variations that:
- Rephrase the same concept differently
- Use synonyms or related terms
- Approach the topic from different angles
- Keep the core intent intact

Return only the query variations, no explanations."""

    result = instructor_client.chat.completions.create(
        model="gpt-4o-mini",
        response_model=QueryExpansion,
        messages=[
            {"role": "user", "content": expansion_prompt}
        ],
        temperature=0.7
    )
    
    # Combine original query with expanded variations
    all_queries = [user_query] + result.expanded_queries
    return all_queries


def retrieve_chunks(file_id: str, user_query: str, top_k: int = 10) -> str:
    """Retrieve relevant chunks using multi-query expansion.
    
    Args:
        file_id: Document collection ID
        user_query: User's topic query
        top_k: Number of chunks to retrieve per query
        
    Returns:
        Combined and deduplicated chunks as text
    """
    # Get collection
    collection = chroma_client.get_collection(
        name=file_id,
        embedding_function=openai_ef
    )
    
    # Expand query into multiple variations
    queries = expand_query(user_query)
    
    # Retrieve chunks for each query variation
    all_chunk_ids: Set[str] = set()
    chunk_data = {}
    
    for query in queries:
        results = collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        # Store chunks and their IDs
        if results["ids"] and results["documents"]:
            for chunk_id, chunk_text in zip(results["ids"][0], results["documents"][0]):
                if chunk_id not in all_chunk_ids:
                    all_chunk_ids.add(chunk_id)
                    chunk_data[chunk_id] = chunk_text
    
    # Sort by chunk index to maintain document order
    sorted_chunks = sorted(
        chunk_data.items(),
        key=lambda x: int(x[0].split("_chunk_")[1])
    )
    
    # Combine chunks into single text
    combined_text = "\n\n".join([chunk for _, chunk in sorted_chunks])
    
    return combined_text


def delete_vector_store(file_id: str) -> None:
    """Delete ChromaDB collection for a document.
    
    Args:
        file_id: Document collection ID to delete
    """
    try:
        chroma_client.delete_collection(name=file_id)
    except Exception:
        pass  # Collection doesn't exist or already deleted
