"""
Search Schemas - Pydantic Models for Web Search

Defines the data structures for search operations:
- SearchResult: Individual search result from Tavily or Exa API
- CombinedSearchResults: Aggregated and deduplicated results from multiple sources

All models use Pydantic for validation and structured data handling.
"""

from typing import List
from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """Individual search result from Tavily or Exa."""
    
    title: str = Field(..., description="Title of the search result")
    url: str = Field(..., description="URL of the search result")
    content: str = Field(..., description="Content snippet from the search result")
    source: str = Field(..., description="Source API (tavily or exa)")


class CombinedSearchResults(BaseModel):
    """Aggregated and deduplicated search results from multiple sources."""
    
    results: List[SearchResult] = Field(default_factory=list)
    total_results: int = Field(..., description="Total count after deduplication")
