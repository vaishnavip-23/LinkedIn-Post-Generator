"""
Document Processor - PDF extraction and validation

Handles PDF text extraction, token counting, and validation.
"""

import tiktoken
from pypdf import PdfReader

from backend.models.schema import DocumentValidation
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


def validate_document(text: str, file_size_bytes: int) -> DocumentValidation:
    """Validate document and determine processing tier.

    Args:
        text: Extracted document text
        file_size_bytes: File size in bytes

    Returns:
        DocumentValidation with validation results
    """
    # Validate file size
    try:
        validate_file_size(file_size_bytes)
    except ValueError as e:
        return DocumentValidation(
            is_valid=False,
            token_count=0,
            tier="",
            error_message=str(e)
        )

    # Check for empty document
    if not text.strip():
        return DocumentValidation(
            is_valid=False,
            token_count=0,
            tier="",
            error_message="Unable to extract text from PDF. The file may be empty or image-based."
        )

    # Count tokens
    token_count = count_tokens(text)

    # Validate token count
    if token_count > MAX_TOKEN_LIMIT:
        return DocumentValidation(
            is_valid=False,
            token_count=token_count,
            tier="",
            error_message=f"Document too long ({token_count:,} tokens). Maximum allowed is {MAX_TOKEN_LIMIT:,} tokens."
        )

    # Determine tier
    tier = "direct" if token_count <= DIRECT_TOKEN_LIMIT else "rag"

    return DocumentValidation(
        is_valid=True,
        token_count=token_count,
        tier=tier,
        error_message=None
    )
