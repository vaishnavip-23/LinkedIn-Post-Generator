"""
Document Processor - PDF extraction and validation

Handles PDF text extraction, token counting, and validation.
"""

import tiktoken
from pypdf import PdfReader

from backend.tools.file_search.config import (
    MAX_FILE_SIZE_BYTES,
    MAX_TOKEN_LIMIT,
    DIRECT_TOKEN_LIMIT,
    LLM_MODEL
)


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract all text from PDF file.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Extracted text as string
    """
    reader = PdfReader(pdf_path)
    text_parts = []

    for page in reader.pages:
        text = page.extract_text()
        if text:
            text_parts.append(text)

    return "\n\n".join(text_parts)


def count_tokens(text: str) -> int:
    """Count tokens in text using tiktoken.

    Args:
        text: Text to count tokens for

    Returns:
        Token count
    """
    encoding = tiktoken.encoding_for_model(LLM_MODEL)
    tokens = encoding.encode(text)
    return len(tokens)


def validate_file_size(size_bytes: int) -> None:
    """Validate file size is within limits.

    Args:
        size_bytes: File size in bytes

    Raises:
        ValueError: If file exceeds size limit
    """
    if size_bytes > MAX_FILE_SIZE_BYTES:
        size_mb = size_bytes / (1024 * 1024)
        raise ValueError(
            f"File too large ({size_mb:.1f}MB). Maximum allowed is {MAX_FILE_SIZE_BYTES / (1024 * 1024):.0f}MB."
        )


def validate_token_count(token_count: int) -> None:
    """Validate token count is within limits.
    
    Args:
        token_count: Number of tokens in document
        
    Raises:
        ValueError: If tokens exceed MAX_TOKEN_LIMIT
    """
    if token_count > MAX_TOKEN_LIMIT:
        raise ValueError(
            f"Document too long ({token_count:,} tokens). "
            f"Maximum allowed is {MAX_TOKEN_LIMIT:,} tokens (~80-100 pages). "
            f"Please upload a shorter document."
        )


def determine_tier(token_count: int) -> str:
    """Determine processing tier based on token count.
    
    Args:
        token_count: Number of tokens in document
        
    Returns:
        'direct' if ≤80k tokens, 'rag' if >80k tokens
    """
    return "direct" if token_count <= DIRECT_TOKEN_LIMIT else "rag"


def truncate_text(text: str, max_tokens: int = 100_000, model: str = "gpt-4o-mini") -> str:
    """Truncate text to fit within token limit.
    
    Args:
        text: Text to truncate
        max_tokens: Maximum allowed tokens (default: 100k for GPT-4o mini)
        model: Model name for encoding (default: gpt-4o-mini)
        
    Returns:
        Truncated text if exceeds limit, otherwise original text
    """
    token_count = count_tokens(text)
    
    if token_count <= max_tokens:
        return text
    
    # Truncate tokens and decode back to text
    encoding = tiktoken.encoding_for_model(model)
    tokens = encoding.encode(text)
    truncated_tokens = tokens[:max_tokens]
    truncated_text = encoding.decode(truncated_tokens)
    
    return truncated_text + "\n\n[Content truncated to fit token limit]"
