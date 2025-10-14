"""
Post Generation Service - LinkedIn Content Creation

Generates professional LinkedIn posts using OpenAI's GPT-4o-mini with Instructor
for structured outputs. Takes web search results and synthesizes them into
engaging, LinkedIn-optimized posts following best practices.

Key Features:
- Structured output using Instructor + Pydantic
- LinkedIn best practices system prompt
- Contextual post generation from search results
- Returns validated LinkedInPost objects with content, hashtags, and key points
"""

import os
import instructor
from openai import OpenAI

from backend.linkedin_prompts import LINKEDIN_SYSTEM_PROMPT
from backend.models.post_schemas import LinkedInPost
from backend.models.search_schemas import CombinedSearchResults


class PostGenerationService:
    """Service for generating LinkedIn posts using GPT-4o-mini with Instructor."""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable is required")
        
        self.client = instructor.from_openai(OpenAI(api_key=api_key))
    
    def generate_post(self, query: str, search_results: CombinedSearchResults) -> LinkedInPost:
        """
        Generate a LinkedIn post from search results using structured output.
        
        Args:
            query: User's original topic/prompt
            search_results: Combined and deduplicated search results
            
        Returns:
            LinkedInPost with structured content, hashtags, and key points
        """
        context = self._format_research_context(search_results)
        user_prompt = self._build_generation_prompt(query, context)
        
        return self.client.chat.completions.create(
            model="gpt-4o-mini",
            response_model=LinkedInPost,
            messages=[
                {"role": "system", "content": LINKEDIN_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
    
    def _format_research_context(self, search_results: CombinedSearchResults) -> str:
        """Format search results into structured research context."""
        return "\n---\n".join([
            f"Source {idx} ({result.source}):\n"
            f"Title: {result.title}\n"
            f"URL: {result.url}\n"
            f"Content: {result.content}"
            for idx, result in enumerate(search_results.results, 1)
        ])
    
    def _build_generation_prompt(self, query: str, context: str) -> str:
        """Build the user prompt for post generation."""
        return f"""Topic: {query}

Research Content:
{context}

Synthesize this research into a compelling LinkedIn post that provides unique insights and value."""
