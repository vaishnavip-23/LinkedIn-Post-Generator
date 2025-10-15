"""
Document Utilities - PDF extraction and token counting

Simple utilities for processing PDF files and counting tokens.
"""

import tiktoken
from pypdf import PdfReader


# Token limits
MAX_FILE_SIZE_BYTES = 3 * 1024 * 1024  # 3 MB
DIRECT_TOKEN_LIMIT = 80_000  # Direct processing if ≤80k tokens
MAX_TOKEN_LIMIT = 120_000  # Hard limit


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


def count_tokens(text: str, model: str = "gpt-4o-mini") -> int:
    """Count tokens in text using tiktoken.
    
    Args:
        text: Text to count tokens for
        model: Model name for encoding (default: gpt-4o-mini)
        
    Returns:
        Token count
    """
    # Get encoding for the model (gpt-4o uses cl100k_base)
    encoding = tiktoken.encoding_for_model(model)
    tokens = encoding.encode(text)
    return len(tokens)


def validate_file_size(size_bytes: int) -> None:
    """Validate file size is within limits.
    
    Args:
        size_bytes: File size in bytes
        
    Raises:
        ValueError: If file exceeds 3MB limit
    """
    if size_bytes > MAX_FILE_SIZE_BYTES:
        size_mb = size_bytes / (1024 * 1024)
        raise ValueError(
            f"File too large ({size_mb:.1f}MB). Maximum allowed is 3MB. "
            f"Please upload a smaller document."
        )


def validate_token_count(token_count: int) -> None:
    """Validate token count is within limits.
    
    Args:
        token_count: Number of tokens in document
        
    Raises:
        ValueError: If tokens exceed 120k limit
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
