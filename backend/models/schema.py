"""
Pydantic Schemas - All Data Models

Consolidated schema definitions for the entire application.
Uses Pydantic for validation and Instructor for structured LLM outputs.

Schema Categories:
- Request/Response: API input/output models
- LinkedIn Post: Post generation models
- Search: Web search result models
- YouTube: Video transcription models
"""

from typing import List, Optional
from urllib.parse import urlparse

from pydantic import BaseModel, Field, HttpUrl, field_validator


# ============================================================================
# API REQUEST/RESPONSE SCHEMAS
# ============================================================================

class LinkedInPostRequest(BaseModel):
    """API request for LinkedIn post generation."""
    
    query: str = Field(
        ..., 
        description="User's topic, question, or YouTube URL",
        min_length=3,
        examples=["AI trends in healthcare", "https://youtube.com/watch?v=abc"]
    )
    conversation_id: Optional[str] = Field(
        None,
        description="Conversation ID for maintaining session context"
    )


class LinkedInPost(BaseModel):
    """Generated LinkedIn post with structured content.
    
    This is the output from the LLM content generation.
    The content should follow LinkedIn best practices:
    - Strong hook in first 1-2 lines
    - 3-5 short paragraphs with single line breaks
    - Engaging CTA at the end
    - 150-300 words total
    - Hashtags MUST be in separate field, NOT in content
    """
    
    content: str = Field(
        ...,
        description="LinkedIn post text WITHOUT hashtags. Do not include any hashtags in this field. Just the post content.",
        min_length=100,
        max_length=2600
    )
    hashtags: List[str] = Field(
        ...,
        description="Array of 3-5 hashtag strings WITHOUT # symbol (e.g., ['AI', 'TechForGood', 'Innovation']). Do not include these in content field.",
        min_length=3,
        max_length=5
    )


class LinkedInPostResponse(BaseModel):
    """API response containing generated LinkedIn post and metadata.
    
    This is the final response sent to the client, wrapping the generated
    post with metadata about how it was created.
    """
    
    post: LinkedInPost = Field(..., description="The generated LinkedIn post")
    tool_used: Optional[str] = Field(
        None,
        description="Which tool was used: 'web_search' or 'youtube_transcribe'"
    )
    conversation_id: str = Field(
        ...,
        description="Conversation ID for session tracking"
    )


# ============================================================================
# WEB SEARCH SCHEMAS
# ============================================================================

class SearchResult(BaseModel):
    """Individual search result from Tavily or Exa API."""
    
    title: str = Field(..., description="Article/page title")
    url: str = Field(..., description="Source URL")
    content: str = Field(..., description="Content snippet")
    source: str = Field(..., description="API source (tavily or exa)")


# ============================================================================
# YOUTUBE SCHEMAS
# ============================================================================

class YouTubeContent(BaseModel):
    """Transcribed YouTube video content."""
    
    video_url: HttpUrl = Field(..., description="YouTube video URL")
    title: str = Field(..., description="Video title", min_length=1)
    author: Optional[str] = Field(None, description="Channel name")
    duration_seconds: int = Field(..., description="Video length in seconds", ge=1)
    transcript: str = Field(..., description="Full video transcript", min_length=1)

    @field_validator("video_url")
    @classmethod
    def validate_youtube_url(cls, url: HttpUrl) -> HttpUrl:
        host = urlparse(str(url)).netloc.lower().split(":", 1)[0]
        if not (host.endswith("youtube.com") or host.endswith("youtu.be")):
            raise ValueError("video_url must be a valid YouTube URL")
        return url


# ============================================================================
# DOCUMENT SCHEMAS
# ============================================================================

class DocumentMetadata(BaseModel):
    """Metadata returned after document upload."""
    
    file_id: str = Field(..., description="Unique identifier for uploaded document")
    filename: str = Field(..., description="Original filename")
    size_bytes: int = Field(..., description="File size in bytes")
    token_count: int = Field(..., description="Total tokens in document")
    tier: str = Field(..., description="Processing tier: 'direct' or 'rag'")
    message: str = Field(..., description="User-facing message about next steps")


class DocumentContent(BaseModel):
    """Stored document content with full text or vector store reference."""
    
    file_id: str = Field(..., description="Unique identifier")
    filename: str = Field(..., description="Original filename")
    token_count: int = Field(..., description="Total tokens")
    tier: str = Field(..., description="'direct' or 'rag'")
    full_text: Optional[str] = Field(None, description="Full text for direct tier")
    vector_store_id: Optional[str] = Field(None, description="ChromaDB collection ID for RAG tier")


class QueryExpansion(BaseModel):
    """Multi-query expansion for better RAG retrieval."""
    
    original_query: str = Field(..., description="User's original query")
    expanded_queries: List[str] = Field(
        ..., 
        description="Exactly 3 semantically similar query variations",
        min_length=3,
        max_length=3
    )



