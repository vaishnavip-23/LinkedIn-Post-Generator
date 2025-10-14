"""
LinkedIn Post Schemas - Pydantic Models for Post Generation

Defines the data structures for LinkedIn post operations:
- LinkedInPostRequest: API request model containing the topic/query
- LinkedInPost: Generated post with content, hashtags, and key points
- LinkedInPostResponse: API response wrapper

All models enforce structured data with Instructor + Pydantic validation.
"""

from typing import List
from pydantic import BaseModel, Field


class LinkedInPostRequest(BaseModel):
    """Request model for LinkedIn post generation."""
    
    query: str = Field(..., description="Topic or prompt for post generation")


class LinkedInPost(BaseModel):
    """Structured LinkedIn post with content and metadata."""
    
    content: str = Field(..., description="Formatted LinkedIn post content")
    hashtags: List[str] = Field(default_factory=list, description="Relevant hashtags")
    key_points: List[str] = Field(default_factory=list, description="Key insights covered")


class LinkedInPostResponse(BaseModel):
    """Response model containing the generated LinkedIn post."""
    
    post: LinkedInPost
