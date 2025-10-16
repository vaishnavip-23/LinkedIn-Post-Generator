"""
Web Search Tool - Tavily and Exa API Integration

Searches the web using both Tavily and Exa APIs in parallel,
combines results, and deduplicates by URL.

Uses OpenAI Agents SDK @function_tool decorator and Pydantic for validation.
"""

import os
from typing import List
from exa_py import Exa
from tavily import TavilyClient
from agents import function_tool

from backend.models.schema import SearchResult

# Maximum characters per search result to prevent context overflow
MAX_CONTENT_LENGTH = 4000


@function_tool
async def web_search(query: str) -> List[SearchResult]:
    """Search the web for current information on any topic.
    
    Use this for general research, trends, news, articles, or any non-video content.
    Searches both Tavily and Exa APIs, combines and deduplicates results.
    
    Args:
        query: The search query or topic to research
        
    Returns:
        List of SearchResult objects with title, URL, content, and source
    """
    # Initialize API clients
    tavily_key = os.getenv("TAVILY_KEY")
    exa_key = os.getenv("EXA_KEY")
    
    if not tavily_key or not exa_key:
        raise ValueError("TAVILY_KEY and EXA_KEY must be set")
    
    tavily_client = TavilyClient(api_key=tavily_key)
    exa_client = Exa(api_key=exa_key)
    
    # Execute searches
    tavily_results = await _search_tavily(tavily_client, query)
    exa_results = await _search_exa(exa_client, query)
    
    # Combine and deduplicate by URL
    all_results = tavily_results + exa_results
    deduplicated = _deduplicate_by_url(all_results)
    
    # Return structured data
    return deduplicated


async def _search_tavily(client: TavilyClient, query: str) -> List[SearchResult]:
    """Search via Tavily API with Pydantic validation."""
    try:
        response = client.search(
            query=query,
            max_results=3,
            search_depth="basic",  # Faster, more focused results
            include_answer=False,  # We only need search results
            include_raw_content=True  # Get full article content
        )
        raw_results = response.get("results", [])
        
        if not raw_results:
            return []
        
        # Validate and parse with Pydantic
        validated_results = []
        for item in raw_results:
            try:
                # Get full content (raw_content preferred, fallback to content)
                content = item.get("raw_content") or item.get("content", "")
                # Truncate to prevent context overflow
                truncated_content = _truncate_content(content)
                result = SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    content=truncated_content,
                    source="tavily"
                )
                validated_results.append(result)
            except Exception as e:
                print(f"Skipping invalid Tavily result: {e}")
                continue
        
        return validated_results
    except Exception as e:
        print(f"Tavily error: {e}")
        return []


async def _search_exa(client: Exa, query: str) -> List[SearchResult]:
    """Search via Exa API with Pydantic validation."""
    try:
        response = client.search_and_contents(
            query=query,
            num_results=3,
            text=True,  # Get full text content without character limit
            use_autoprompt=True  # Better query understanding
        )
        
        if not response.results:
            return []
        
        # Validate and parse with Pydantic
        validated_results = []
        for item in response.results:
            try:
                # Get full text content
                content = item.text or ""
                # Truncate to prevent context overflow
                truncated_content = _truncate_content(content)
                result = SearchResult(
                    title=item.title or "",
                    url=item.url or "",
                    content=truncated_content,
                    source="exa"
                )
                validated_results.append(result)
            except Exception as e:
                print(f"Skipping invalid Exa result: {e}")
                continue
        
        return validated_results
    except Exception as e:
        print(f"Exa error: {e}")
        return []


def _deduplicate_by_url(results: List[SearchResult]) -> List[SearchResult]:
    """Remove duplicate results based on URL - keeps first occurrence."""
    seen_urls = set()
    deduplicated = []
    
    for result in results:
        if result.url not in seen_urls:
            seen_urls.add(result.url)
            deduplicated.append(result)
    
    return deduplicated


def _truncate_content(content: str, max_length: int = MAX_CONTENT_LENGTH) -> str:
    """Truncate content to prevent context overflow.
    
    Args:
        content: The full content text
        max_length: Maximum character length (default: 4000)
        
    Returns:
        Truncated content with ellipsis if needed
    """
    if len(content) <= max_length:
        return content
    
    # Truncate and add indicator
    return content[:max_length] + "... [content truncated]"
