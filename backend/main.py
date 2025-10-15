"""
Main Application - LinkedIn Content Research Agent

Single entry point for the FastAPI application. Uses OpenAI's function calling
to route requests to the appropriate tool (web_search or youtube_transcribe),
then generates LinkedIn posts using Instructor for structured outputs.

Architecture:
1. User submits query via POST /api/generate-post
2. OpenAI GPT-4o-mini with function calling selects appropriate tool
3. Tool executes and returns formatted research data
4. Instructor generates structured LinkedIn post
5. Response returned to user

Tools are registered via decorators in the tools/ directory.
"""

import json
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import instructor
import logfire

from backend.models.schema import (
    LinkedInPostRequest,
    LinkedInPostResponse,
    LinkedInPost
)
from backend.prompts import LINKEDIN_SYSTEM_PROMPT
from backend.tools.registry import get_all_tools, get_tool

# Import tools to trigger decorator registration
from backend.tools import web_search, youtube_transcribe

load_dotenv()

# Configure Logfire for tracing
logfire.configure()
logfire.instrument_openai()

# Initialize FastAPI
app = FastAPI(
    title="LinkedIn Content Research Agent",
    description="AI agent with tools for web search and YouTube transcription",
    version="3.0.0"
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

# Initialize OpenAI clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
instructor_client = instructor.from_openai(openai_client)


@app.get("/")
async def root():
    """Health check and API information."""
    return {
        "status": "active",
        "service": "LinkedIn Content Research Agent",
        "version": "3.0.0",
        "tools_available": ["web_search", "youtube_transcribe"],
        "endpoint": "/api/generate-post"
    }


@app.post("/api/generate-post", response_model=LinkedInPostResponse)
async def generate_post(request: LinkedInPostRequest):
    """
    Generate a LinkedIn post using AI agent with automatic tool selection.
    
    Flow:
    1. Agent analyzes query with GPT-4o-mini + function calling
    2. Selects tool: web_search OR youtube_transcribe
    3. Executes tool and gathers research
    4. Generates LinkedIn post with Instructor
    
    Examples:
        - "AI trends" → web_search → LinkedIn post
        - "https://youtube.com/watch?v=xyz" → youtube_transcribe → LinkedIn post
    
    Returns:
        LinkedInPostResponse with generated post
    """
    try:
        # Step 1: Agent selects and calls appropriate tool
        tool_result = await _execute_agent_tool_selection(request.query)
        
        if not tool_result["success"]:
            raise HTTPException(
                status_code=400, 
                detail=tool_result.get("error", "Tool execution failed")
            )
        
        # Step 2: Generate LinkedIn post with Instructor
        linkedin_post = _generate_linkedin_post(
            query=request.query,
            research_data=tool_result["data"]
        )
        
        # Step 3: Return response
        return LinkedInPostResponse(
            post=linkedin_post,
            tool_used=tool_result.get("tool_name")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


async def _execute_agent_tool_selection(query: str) -> dict:
    """
    Use OpenAI function calling to select and execute the right tool.
    
    Args:
        query: User's input query
        
    Returns:
        Dictionary with tool execution results
    """
    # Get all registered tool schemas
    tools = get_all_tools()
    
    # Call GPT-4o-mini with function calling
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are an AI agent that selects the right tool for LinkedIn post research. Choose web_search for general topics, youtube_transcribe for YouTube URLs."
            },
            {
                "role": "user",
                "content": query
            }
        ],
        tools=tools,
        tool_choice="auto"
    )
    
    # Extract tool call
    message = response.choices[0].message
    
    if not message.tool_calls:
        return {
            "success": False,
            "error": "No appropriate tool found for this query"
        }
    
    # Get the selected tool
    tool_call = message.tool_calls[0]
    function_name = tool_call.function.name
    function_args = json.loads(tool_call.function.arguments)
    
    # Execute the tool
    tool_function = get_tool(function_name)
    
    if not tool_function:
        return {
            "success": False,
            "error": f"Tool '{function_name}' not found"
        }
    
    # Call the tool with arguments
    result = await tool_function(**function_args)
    
    return result


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
