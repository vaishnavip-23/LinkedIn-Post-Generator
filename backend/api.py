"""
FastAPI Application - LinkedIn Content Research Agent

This is the main API server that handles LinkedIn post generation requests.
It coordinates between web search services (Tavily & Exa) and post generation
using GPT-4o-mini with Instructor for structured outputs.

Endpoints:
- GET  /                            : Health check
- POST /api/generate-linkedin-post  : Generate LinkedIn post from topic query
"""

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.models.post_schemas import LinkedInPostRequest, LinkedInPostResponse
from backend.services.post_generation_service import PostGenerationService
from backend.services.web_search_service import WebSearchService

load_dotenv()

app = FastAPI(
    title="LinkedIn Content Research Agent",
    description="AI-powered LinkedIn post generation using web research from Tavily and Exa",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

search_service = WebSearchService()
post_service = PostGenerationService()


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "active",
        "service": "LinkedIn Content Research Agent",
        "endpoint": "/api/generate-linkedin-post"
    }


@app.post("/api/generate-linkedin-post", response_model=LinkedInPostResponse)
async def generate_linkedin_post(request: LinkedInPostRequest):
    """
    Generate a LinkedIn post from a topic query.
    
    Process:
    1. Searches topic across Tavily and Exa APIs
    2. Combines and deduplicates results
    3. Generates LinkedIn post using GPT-4o-mini with Instructor
    
    Returns structured LinkedIn post with content, hashtags, and key points.
    """
    try:
        search_results = await search_service.search(request.query)
        
        if search_results.total_results == 0:
            raise HTTPException(
                status_code=404,
                detail="No search results found for the given query"
            )
        
        linkedin_post = post_service.generate_post(request.query, search_results)
        
        return LinkedInPostResponse(post=linkedin_post)
    
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc