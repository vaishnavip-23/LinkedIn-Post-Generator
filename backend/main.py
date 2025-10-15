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
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import instructor
import logfire
from agents import Agent, Runner

from backend.models.schema import (
    LinkedInPostRequest,
    LinkedInPostResponse,
    LinkedInPost,
    DocumentMetadata,
    DocumentContent
)
from backend.prompts import LINKEDIN_SYSTEM_PROMPT, DOCUMENT_GROUNDING_PROMPT
from backend.tools.web_search import web_search
from backend.tools.youtube_transcribe import youtube_transcribe
from backend.tools.file_search.tool import file_search, set_document_store
from backend.tools.file_search.rag import create_vector_store, delete_vector_store
from backend.tools.file_search.document_processor import (
    extract_text_from_pdf,
    count_tokens,
    validate_file_size,
    validate_token_count,
    determine_tier,
    truncate_text
)

load_dotenv()

# In-memory storage (use Redis/DB for production)
conversation_store: Dict[str, List[Dict[str, str]]] = {}
document_store: Dict[str, DocumentContent] = {}

# Initialize document store reference in file_search tool
set_document_store(document_store)

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

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DECISION ORDER (Follow this EXACT sequence)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 1: CHECK IF THIS IS A REFINEMENT REQUEST (Check CURRENT user message ONLY)

Is the CURRENT request asking to modify/refine a previous post?

REFINEMENT INDICATORS (if ANY of these are present → NO TOOL NEEDED):
✓ "add more..." / "add some..." / "include..."
✓ "remove..." / "delete..." / "take out..."
✓ "make it more..." / "make it less..."
✓ "shorten" / "shorter" / "longer" / "expand"
✓ "change the tone" / "more formal" / "more casual"
✓ "more emojis" / "fewer hashtags" / "different hashtags"
✓ "rewrite" / "rephrase" / "improve"

→ If REFINEMENT detected: Use conversation context to refine. DO NOT CALL ANY TOOL.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 2: IF NOT REFINEMENT, CHECK FOR NEW CONTENT REQUEST

Look at CURRENT user message ONLY (ignore conversation history for this check):

A) Does CURRENT message contain [file_id: ...]?
   → YES: Extract file_id and topic → Call file_search(file_id, topic_query)
   → Example: "[file_id: abc-123] climate change" → file_search("abc-123", "climate change")

B) Does CURRENT message contain a YouTube URL (youtube.com or youtu.be)?
   → YES: Call youtube_transcribe(video_url)

C) None of the above?
   → Call web_search(query) for general topics, trends, news

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EXAMPLES:

Example 1 - REFINEMENT (NO TOOL):
Previous: "User: [file_id: abc-123] climate change"
Current: "add more emojis"
→ This is REFINEMENT → Use conversation context → NO TOOL

Example 2 - REFINEMENT (NO TOOL):
Previous: "User: AI trends"
Current: "make it more formal"
→ This is REFINEMENT → Use conversation context → NO TOOL

Example 3 - NEW CONTENT (USE TOOL):
Current: "[file_id: abc-123] renewable energy"
→ This is NEW CONTENT → Call file_search("abc-123", "renewable energy")

Example 4 - NEW CONTENT (USE TOOL):
Current: "cryptocurrency trends 2024"
→ This is NEW CONTENT → Call web_search("cryptocurrency trends 2024")

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CRITICAL RULES:
1. ALWAYS check for refinement FIRST before checking for file_id/URL
2. Only look at CURRENT user message, not conversation history, to detect file_id/URL
3. If refinement detected, NEVER call any tool
4. Each tool call is expensive - only use when absolutely necessary
5. Return tool results as-is - content generation system will process them

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━""",
    model="gpt-4o-mini",
    tools=[web_search, youtube_transcribe, file_search]
)


@app.get("/")
async def root():
    """Health check and API information."""
    return {
        "status": "active",
        "service": "LinkedIn Content Research Agent",
        "version": "5.0.0",
        "tools_available": ["web_search", "youtube_transcribe", "file_search"],
        "endpoints": {
            "upload_document": "/api/upload-document",
            "generate_post": "/api/generate-post",
            "clear_conversation": "/api/conversation/{conversation_id}"
        }
    }


@app.post("/api/upload-document", response_model=DocumentMetadata)
async def upload_document(file: UploadFile = File(...)):
    """Upload and process PDF document for LinkedIn post generation.
    
    Flow:
    1. Validate file size (≤3MB)
    2. Extract text from PDF
    3. Count tokens
    4. Determine tier (direct ≤80k or RAG >80k)
    5. Store in memory (full text or vector store)
    
    Returns:
        DocumentMetadata with file_id, token count, tier, and next steps message
    """
    # Validate PDF format
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported. Please upload a PDF document."
        )
    
    try:
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Validate file size (3MB limit)
        validate_file_size(file_size)
        
        # Save temporarily for extraction
        temp_path = f"/tmp/{uuid.uuid4()}.pdf"
        with open(temp_path, "wb") as f:
            f.write(content)
        
        # Extract text from PDF
        text = extract_text_from_pdf(temp_path)
        
        # Clean up temp file
        os.remove(temp_path)
        
        if not text.strip():
            raise HTTPException(
                status_code=400,
                detail="Unable to extract text from PDF. The file may be empty or image-based."
            )
        
        # Count tokens
        token_count = count_tokens(text)
        
        # Validate token count (120k limit)
        validate_token_count(token_count)
        
        # Determine processing tier
        tier = determine_tier(token_count)
        
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        
        # Process based on tier
        if tier == "direct":
            # Store full text in memory
            doc = DocumentContent(
                file_id=file_id,
                filename=file.filename,
                token_count=token_count,
                tier=tier,
                full_text=text,
                vector_store_id=None
            )
            message = "Document uploaded! What specific topic or angle would you like to create a LinkedIn post about?"
        
        else:  # RAG tier
            # Create vector store with embeddings
            vector_store_id = create_vector_store(file_id, text)
            
            doc = DocumentContent(
                file_id=file_id,
                filename=file.filename,
                token_count=token_count,
                tier=tier,
                full_text=None,
                vector_store_id=vector_store_id
            )
            message = "Large document uploaded and indexed! What specific topic or angle would you like to create a LinkedIn post about?"
        
        # Store document
        document_store[file_id] = doc
        
        # Return metadata
        return DocumentMetadata(
            file_id=file_id,
            filename=file.filename,
            size_bytes=file_size,
            token_count=token_count,
            tier=tier,
            message=message
        )
    
    except ValueError as e:
        # Handle validation errors (file size, token count)
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}") from e


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
        
        # Truncate research_data if it exceeds 100k tokens (for GPT-4o mini)
        research_data = truncate_text(research_data, max_tokens=100_000)
        
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
    # Check if this is from a document (file_search tool)
    is_document = "Document:" in research_data and ("Full document content:" in research_data or "Relevant sections retrieved" in research_data)
    
    # Build system prompt with document grounding if needed
    system_prompt = LINKEDIN_SYSTEM_PROMPT
    if is_document:
        system_prompt = LINKEDIN_SYSTEM_PROMPT + "\n\n" + DOCUMENT_GROUNDING_PROMPT
    
    user_prompt = f"""Topic: {query}

Research Content:
{research_data}

Create a compelling LinkedIn post that synthesizes this research following best practices."""
    
    if is_document:
        user_prompt += "\n\nREMINDER: Only use information explicitly stated in the document above. If the topic is not covered, you can still generate a response explaining this - use the content field to explain the topic is not in the document."
    
    try:
        linkedin_post = instructor_client.chat.completions.create(
            model="gpt-4o-mini",
            response_model=LinkedInPost,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        
        # Check if the post is actually a "not found" message
        if is_document and ("cannot create" in linkedin_post.content.lower() or "not covered in" in linkedin_post.content.lower() or "not present in" in linkedin_post.content.lower()):
            # This is an error message, raise it
            raise ValueError(linkedin_post.content)
        
        return linkedin_post
    except Exception as e:
        # If generation fails or topic not in document, raise clear error
        if "cannot create" in str(e).lower() or "not covered" in str(e).lower() or "not present" in str(e).lower():
            raise ValueError(str(e))
        raise


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
