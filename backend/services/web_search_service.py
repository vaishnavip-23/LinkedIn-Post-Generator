"""
Web Search Service - Tavily and Exa API Integration

Handles all web search operations by coordinating parallel searches across
Tavily and Exa APIs. Combines results from both sources and deduplicates
them by URL to provide comprehensive, unique search results.

Key Features:
- Parallel API calls to Tavily and Exa
- URL-based deduplication
- Error handling for individual API failures
- Returns structured SearchResult objects
"""

import os
from typing import List
from exa_py import Exa
from tavily import TavilyClient

from backend.models.search_schemas import CombinedSearchResults, SearchResult


class WebSearchService:
    """Service for executing parallel web searches across Tavily and Exa APIs."""
    
    def __init__(self):
        self._validate_api_keys()
        self.tavily_client = TavilyClient(api_key=os.getenv("TAVILY_KEY"))
        self.exa_client = Exa(api_key=os.getenv("EXA_KEY"))
    
    def _validate_api_keys(self) -> None:
        """Validate required API keys are present."""
        if not os.getenv("TAVILY_KEY"):
            raise RuntimeError("TAVILY_KEY environment variable is required")
        if not os.getenv("EXA_KEY"):
            raise RuntimeError("EXA_KEY environment variable is required")
    
    async def search_tavily(self, query: str) -> List[SearchResult]:
        """Execute search via Tavily API."""
        try:
            response = self.tavily_client.search(query=query, max_results=5)
            return [
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    content=item.get("content", ""),
                    source="tavily"
                )
                for item in response.get("results", [])
            ]
        except Exception as e:
            print(f"Tavily search error: {e}")
            return []
    
    async def search_exa(self, query: str) -> List[SearchResult]:
        """Execute search via Exa API."""
        try:
            response = self.exa_client.search_and_contents(
                query=query,
                num_results=5,
                text=True
            )
            return [
                SearchResult(
                    title=item.title or "",
                    url=item.url or "",
                    content=item.text or "",
                    source="exa"
                )
                for item in response.results
            ]
        except Exception as e:
            print(f"Exa search error: {e}")
            return []
    
    def _deduplicate_by_url(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate results based on URL."""
        seen_urls = set()
        deduplicated = []
        
        for result in results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                deduplicated.append(result)
        
        return deduplicated
    
    async def search(self, query: str) -> CombinedSearchResults:
        """
        Execute parallel searches across Tavily and Exa, then combine and deduplicate results.
        
        Args:
            query: Search query string
            
        Returns:
            CombinedSearchResults with deduplicated results from both APIs
        """
        tavily_results = await self.search_tavily(query)
        exa_results = await self.search_exa(query)
        
        all_results = tavily_results + exa_results
        deduplicated_results = self._deduplicate_by_url(all_results)
        
        return CombinedSearchResults(
            results=deduplicated_results,
            total_results=len(deduplicated_results)
        )
