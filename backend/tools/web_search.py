"""
Web Search Tool - Tavily and Exa API Integration

Searches the web using both Tavily and Exa APIs in parallel,
combines results, and deduplicates by URL.

Decorated with @tool for automatic registration with the AI agent.
"""

import os
from typing import List
from exa_py import Exa
from tavily import TavilyClient

from backend.models.schema import SearchResult, WebSearchResult
from backend.tools.registry import tool


@tool(
    name="web_search",
    description="Search the web using Tavily and Exa APIs for current information on any topic. Use this for general research, trends, news, articles, or any non-video content.",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query or topic to research"
            }
        },
        "required": ["query"]
    }
)
async def web_search(query: str) -> dict:
    """
    Execute web search across Tavily and Exa, return deduplicated results.
    
    Args:
        query: Search query string
        
    Returns:
        Dictionary with success status and formatted search results
    """
    # Initialize clients
    tavily_key = os.getenv("TAVILY_KEY")
    exa_key = os.getenv("EXA_KEY")
    
    if not tavily_key or not exa_key:
        return {
            "success": False,
            "error": "API keys not configured",
            "data": ""
        }
    
    tavily_client = TavilyClient(api_key=tavily_key)
    exa_client = Exa(api_key=exa_key)
    
    # Execute searches in parallel
    tavily_results = await _search_tavily(tavily_client, query)
    exa_results = await _search_exa(exa_client, query)
    
    # Combine and deduplicate
    all_results = tavily_results + exa_results
    deduplicated = _deduplicate_by_url(all_results)
    
    # Format results
    web_search_result = WebSearchResult(
        results=deduplicated,
        total_results=len(deduplicated)
    )
    
    # Format for post generation
    formatted_data = _format_search_results(web_search_result)
    
    return {
        "success": True,
        "tool_name": "web_search",
        "data": formatted_data
    }


async def _search_tavily(client: TavilyClient, query: str) -> List[SearchResult]:
    """Search via Tavily API."""
    try:
        response = client.search(query=query, max_results=5)
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
        print(f"Tavily error: {e}")
        return []


async def _search_exa(client: Exa, query: str) -> List[SearchResult]:
    """Search via Exa API."""
    try:
        response = client.search_and_contents(
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
        print(f"Exa error: {e}")
        return []


def _deduplicate_by_url(results: List[SearchResult]) -> List[SearchResult]:
    """Remove duplicate results based on URL."""
    seen_urls = set()
    deduplicated = []
    
    for result in results:
        if result.url not in seen_urls:
            seen_urls.add(result.url)
            deduplicated.append(result)
    
    return deduplicated


def _format_search_results(search_result: WebSearchResult) -> str:
    """Format search results for LinkedIn post generation."""
    formatted = []
    
    for idx, result in enumerate(search_result.results, 1):
        formatted.append(
            f"Source {idx} ({result.source}):\n"
            f"Title: {result.title}\n"
            f"URL: {result.url}\n"
            f"Content: {result.content}"
        )
    
    return "\n---\n".join(formatted)
