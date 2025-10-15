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
from pydantic import BaseModel, Field


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


class LinkedInPost(BaseModel):
    """Generated LinkedIn post with structured content."""
    
    content: str = Field(..., description="Complete LinkedIn post text")
    hashtags: List[str] = Field(
        default_factory=list, 
        description="3-5 relevant hashtags"
    )
    key_points: List[str] = Field(
        default_factory=list,
        description="Main insights from the post"
    )


class LinkedInPostResponse(BaseModel):
    """API response containing generated LinkedIn post."""
    
    post: LinkedInPost
    tool_used: Optional[str] = Field(
        None, 
        description="Which tool was used (web_search or youtube_transcribe)"
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


class WebSearchResult(BaseModel):
    """Combined and deduplicated web search results."""
    
    results: List[SearchResult] = Field(default_factory=list)
    total_results: int = Field(..., description="Number of unique results")


# ============================================================================
# YOUTUBE SCHEMAS
# ============================================================================

class YouTubeContent(BaseModel):
    """Transcribed YouTube video content."""
    
    video_url: str = Field(..., description="YouTube video URL")
    title: str = Field(..., description="Video title")
    author: Optional[str] = Field(None, description="Channel name")
    duration_seconds: int = Field(..., description="Video length in seconds")
    transcript: str = Field(..., description="Full video transcript")


# ============================================================================
# TOOL EXECUTION SCHEMAS
# ============================================================================

class ToolExecutionResult(BaseModel):
    """Result from executing any tool."""
    
    tool_name: str = Field(..., description="Name of executed tool")
    success: bool = Field(..., description="Whether execution succeeded")
    data: str = Field(..., description="Formatted result data")
    error: Optional[str] = Field(None, description="Error message if failed")
