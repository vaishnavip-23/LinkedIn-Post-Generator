"""
Main Application - LinkedIn Content Research Agent

Single entry point for the FastAPI application. Uses OpenAI Agents SDK
for tool orchestration and Instructor for structured LinkedIn post generation.

Architecture:
1. User submits query via POST /api/generate-post
2. OpenAI Agent automatically selects and executes appropriate tool
3. Tool returns formatted research data
4. Instructor generates structured LinkedIn post
5. Response returned to user

Tools: web_search (Tavily + Exa) and youtube_transcribe (Whisper API)
"""

import os
import uuid
from typing import Dict, List
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import instructor
import logfire
from agents import Agent, Runner

from backend.models.schema import (
    LinkedInPostRequest,
    LinkedInPostResponse,
    LinkedInPost,
    ConversationMessage
)
from backend.prompts import LINKEDIN_SYSTEM_PROMPT
from backend.tools.web_search import web_search
from backend.tools.youtube_transcribe import youtube_transcribe

load_dotenv()

# In-memory conversation storage (use Redis/DB for production)
conversation_store: Dict[str, List[Dict[str, str]]] = {}

# Configure Logfire for tracing
logfire.configure()
logfire.instrument_openai()
logfire.instrument_openai_agents()

# Initialize FastAPI
app = FastAPI(
    title="LinkedIn Content Research Agent",
    description="AI agent with tools for web search and YouTube transcription",
    version="4.0.0"
)

# Instrument FastAPI with Logfire
logfire.instrument_fastapi(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client for Instructor
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
instructor_client = instructor.from_openai(openai_client)

# Initialize Research Agent with tools
research_agent = Agent(
    name="LinkedIn Research Agent",
    instructions="""You are a research assistant for LinkedIn content creation.

Your job:
1. **Analyze the user's query and conversation history**
2. Determine if this is:
   a) A NEW content request → Use appropriate tool (web_search or youtube_transcribe)
   b) A REFINEMENT request → No tool needed, just refine based on conversation history
   
TOOL SELECTION (for NEW content requests):
- Use youtube_transcribe when query contains a YouTube URL (youtube.com or youtu.be)
- Use web_search for topics, trends, news, research questions
- If youtube_transcribe fails (e.g., video too long), DO NOT try web_search as fallback

REFINEMENT HANDLING (for follow-up requests):
- User asks to "make it more formal", "remove emojis", "shorten it" → NO TOOL, use conversation context
- User asks to "add more examples", "change tone" → NO TOOL, refine the previous post
- Previous LinkedIn post is in conversation history - use it as reference

CRITICAL RULES:
- NEW content requests REQUIRE a tool call
- Refinement requests should NOT call tools
- Each query type has ONE designated tool
- Return tool errors to user - don't attempt fallbacks

Simply return your analysis or tool results - it will be processed by the content generation system.""",
    model="gpt-4o-mini",
    tools=[web_search, youtube_transcribe]
)


@app.get("/")
async def root():
    """Health check and API information."""
    return {
        "status": "active",
        "service": "LinkedIn Content Research Agent",
        "version": "4.0.0",
        "tools_available": ["web_search", "youtube_transcribe"],
        "endpoints": {
            "generate_post": "/api/generate-post",
            "clear_conversation": "/api/conversation/{conversation_id}"
        }
    }


@app.delete("/api/conversation/{conversation_id}")
async def clear_conversation(conversation_id: str):
    """Clear conversation history for a given conversation ID."""
    if conversation_id in conversation_store:
        del conversation_store[conversation_id]
        return {"message": f"Conversation {conversation_id} cleared successfully"}
    return {"message": "Conversation not found (already cleared)"}


@app.post("/api/generate-post", response_model=LinkedInPostResponse)
async def generate_post(request: LinkedInPostRequest):
    """Generate a LinkedIn post using AI agent with automatic tool selection.
    
    Flow:
    1. Agent analyzes query and selects appropriate tool
    2. Tool executes and returns research data
    3. Instructor generates structured LinkedIn post
    
    Examples:
        - "AI trends" → web_search → LinkedIn post
        - "https://youtube.com/watch?v=xyz" → youtube_transcribe → LinkedIn post
    
    Returns:
        LinkedInPostResponse with generated post
    """
    try:
        # Generate or retrieve conversation ID
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        # Build context-aware input by prepending recent history to current query
        context_input = request.query
        if conversation_id in conversation_store:
            stored_history = conversation_store[conversation_id]
            
            if stored_history:
                # Keep last 2 exchanges (4 messages) FULLY for refinements
                recent_full = stored_history[-4:] if len(stored_history) > 4 else stored_history
                # Keep older messages as summaries (truncated) if they exist
                older_summary = stored_history[:-4] if len(stored_history) > 4 else []
                
                context_parts = []
                
                # Add older context as brief summary (only user queries)
                if older_summary:
                    user_queries = [msg['content'][:100] for msg in older_summary if msg['role'] == 'user']
                    if user_queries:
                        context_parts.append(f"Earlier topics discussed: {', '.join(user_queries)}")
                
                # Add recent exchanges FULLY (especially assistant's posts for refinement)
                for msg in recent_full:
                    role = "User" if msg["role"] == "user" else "Assistant"
                    # Keep assistant messages (LinkedIn posts) FULL, truncate only long user messages
                    if msg["role"] == "assistant":
                        content = msg["content"]  # FULL post for refinement
                    else:
                        content = msg["content"][:300] if len(msg["content"]) > 300 else msg["content"]
                    context_parts.append(f"{role}: {content}")
                
                context_str = "\n\n".join(context_parts)
                context_input = f"Previous conversation:\n{context_str}\n\nCurrent request: {request.query}"
        
        # Step 1: Run agent with context-aware input
        agent_result = await Runner.run(
            research_agent,
            context_input
        )
        
        # Check for tool errors in the result
        for item in agent_result.new_items:
            # Check tool output for errors
            if hasattr(item, 'output'):
                output_str = str(item.output)
                if ("too long" in output_str.lower() or 
                    "maximum allowed" in output_str.lower() or 
                    "exceeds limit" in output_str.lower()):
                    # Extract the actual error message (strip agent's wrapper text)
                    if "Error:" in output_str:
                        error_msg = output_str.split("Error:", 1)[1].strip()
                    else:
                        error_msg = output_str.strip()
                    raise HTTPException(status_code=400, detail=error_msg)
            
            # Check message content for errors
            if hasattr(item, 'content') and isinstance(item.content, str):
                if ("too long" in item.content.lower() or 
                    "maximum allowed" in item.content.lower() or 
                    "exceeds limit" in item.content.lower()):
                    raise HTTPException(status_code=400, detail=item.content.strip())
            
            # Check error attribute
            if hasattr(item, 'error') and item.error:
                error_msg = str(item.error)
                if ("too long" in error_msg.lower() or 
                    "maximum allowed" in error_msg.lower() or 
                    "exceeds limit" in error_msg.lower()):
                    raise HTTPException(status_code=400, detail=error_msg.strip())
        
        # Extract research data from agent result
        research_data = str(agent_result.final_output or "")
        
        if not research_data:
            raise HTTPException(
                status_code=400,
                detail="No research data returned from tools"
            )
        
        # Determine which tool was used
        tool_used = None
        for item in agent_result.new_items:
            if hasattr(item, 'tool_name'):
                tool_used = item.tool_name
                break
        
        # Step 2: Generate LinkedIn post with Instructor
        linkedin_post = _generate_linkedin_post(
            query=request.query,
            research_data=research_data
        )
        
        # Step 3: Store conversation history
        assistant_message = f"{linkedin_post.content}\n\n{' '.join(linkedin_post.hashtags)}"
        
        # Initialize conversation if new
        if conversation_id not in conversation_store:
            conversation_store[conversation_id] = []
        
        # Append to conversation history
        conversation_store[conversation_id].append({"role": "user", "content": request.query})
        conversation_store[conversation_id].append({"role": "assistant", "content": assistant_message})
        
        # Step 4: Return response with conversation ID
        return LinkedInPostResponse(
            post=linkedin_post,
            tool_used=tool_used,
            conversation_id=conversation_id
        )
    
    except HTTPException:
        raise
    except ValueError as e:
        # Handle tool validation errors (e.g., video too long)
        error_msg = str(e)
        if "too long" in error_msg.lower() or "exceeds limit" in error_msg.lower():
            raise HTTPException(status_code=400, detail=error_msg) from e
        raise HTTPException(status_code=400, detail=error_msg) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


def _generate_linkedin_post(query: str, research_data: str) -> LinkedInPost:
    """
    Generate LinkedIn post using Instructor for structured output.
    
    Args:
        query: Original user query
        research_data: Formatted research from tool execution
        
    Returns:
        LinkedInPost with structured content
    """
    user_prompt = f"""Topic: {query}

Research Content:
{research_data}

Create a compelling LinkedIn post that synthesizes this research following best practices."""
    
    linkedin_post = instructor_client.chat.completions.create(
        model="gpt-4o-mini",
        response_model=LinkedInPost,
        messages=[
            {"role": "system", "content": LINKEDIN_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7
    )
    
    return linkedin_post


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
