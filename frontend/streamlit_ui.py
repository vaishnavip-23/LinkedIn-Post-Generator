"""
Streamlit User Interface - LinkedIn Content Research Agent

Interactive chat interface for generating LinkedIn posts. Users enter topics
and receive AI-generated, research-backed LinkedIn posts ready to publish.

Features:
- Chat-based interaction
- Real-time post generation
- Copy-to-clipboard functionality
- Backend connectivity status monitoring
- Message history preservation
"""

import asyncio
from typing import Optional

import httpx
import streamlit as st

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="LinkedIn Content Research Agent",
    page_icon="💼",
    layout="wide"
)

st.title("💼 LinkedIn Content Research Agent")
st.markdown("Transform any topic into an engaging LinkedIn post powered by AI research.")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None

if "uploaded_file_id" not in st.session_state:
    st.session_state.uploaded_file_id = None

if "uploaded_filename" not in st.session_state:
    st.session_state.uploaded_filename = None

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


async def generate_linkedin_post(query: str, conversation_id: Optional[str] = None) -> Optional[dict]:
    """Call backend API to generate LinkedIn post from query."""
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            payload = {"query": query}
            if conversation_id:
                payload["conversation_id"] = conversation_id
            
            response = await client.post(
                f"{API_URL}/api/generate-post",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json().get("detail", e.response.text) if e.response.headers.get("content-type") == "application/json" else e.response.text
            
            # Show user-friendly error for validation errors (400)
            if e.response.status_code == 400:
                st.error(error_detail)
                return None
            
            # Show detailed error for server errors (500)
            st.error(f"API Error: {e.response.status_code}")
            with st.expander("Show error details"):
                st.code(error_detail)
            return None
        except httpx.TimeoutException as e:
            st.error(f"Request timed out. The API might be processing a large request. Please try again.")
            return None
        except Exception as e:
            st.error(f"Connection Error: {str(e)}")
            st.info("Make sure the backend is running at http://localhost:8000")
            return None


async def upload_document(file) -> Optional[dict]:
    """Upload PDF document to backend."""
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            files = {"file": (file.name, file, "application/pdf")}
            response = await client.post(
                f"{API_URL}/api/upload-document",
                files=files
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json().get("detail", e.response.text) if e.response.headers.get("content-type") == "application/json" else e.response.text
            st.error(f"Upload Error: {error_detail}")
            return None
        except Exception as e:
            st.error(f"Upload Error: {str(e)}")
            return None


def format_post_output(post_data: dict) -> str:
    """Format LinkedIn post with hashtags for display."""
    post = post_data["post"]
    content = post["content"]
    hashtags = post.get("hashtags", [])
    
    if hashtags:
        # Check if hashtags already include # symbol
        hashtag_str = " ".join(
            tag if tag.startswith("#") else f"#{tag}" 
            for tag in hashtags
        )
        return f"{content}\n\n{hashtag_str}"
    
    return content


# Build query with file_id if document is uploaded
input_placeholder = "What topic would you like to create a LinkedIn post about?" if st.session_state.uploaded_file_id else "Enter a topic, YouTube URL, or upload a PDF document"

if prompt := st.chat_input(input_placeholder):
    # Add file_id context if document is uploaded
    query = prompt
    if st.session_state.uploaded_file_id:
        query = f"[file_id: {st.session_state.uploaded_file_id}] {prompt}"
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        spinner_text = "📄 Analyzing document and generating LinkedIn post..." if st.session_state.uploaded_file_id else "🔍 Researching topic and generating LinkedIn post..."
        with st.spinner(spinner_text):
            result = asyncio.run(generate_linkedin_post(query, st.session_state.conversation_id))
            
            if result:
                # Store conversation ID
                st.session_state.conversation_id = result.get("conversation_id")
                
                linkedin_post = format_post_output(result)
                st.markdown(linkedin_post)
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": linkedin_post
                })
                
                st.success("✅ Post generated successfully!")
                
                # Show tool used (if any)
                if result.get("tool_used"):
                    st.caption(f"📊 Used: {result['tool_used']}")
                
                with st.expander("📋 Copy to Clipboard"):
                    st.code(linkedin_post, language=None)
            else:
                error_msg = "Failed to generate post. Please try again."
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })

st.sidebar.markdown("### 📄 Upload Document")
uploaded_file = st.sidebar.file_uploader(
    "Upload PDF (max 3MB)",
    type=["pdf"],
    help="Upload a PDF document to create LinkedIn posts about specific topics from it"
)

if uploaded_file is not None:
    # Check if this is a new file
    if st.session_state.uploaded_filename != uploaded_file.name:
        with st.spinner("📤 Uploading and processing document..."):
            result = asyncio.run(upload_document(uploaded_file))
            
            if result:
                st.session_state.uploaded_file_id = result["file_id"]
                st.session_state.uploaded_filename = result["filename"]
                
                # Show upload success
                st.sidebar.success(f"✅ {result['filename']} uploaded!")
                st.sidebar.info(f"**Tokens:** {result['token_count']:,}")
                st.sidebar.info(f"**Mode:** {result['tier'].upper()}")
                
                # Add assistant message to chat
                assistant_msg = result["message"]
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": assistant_msg
                })
                st.rerun()
    else:
        # File already uploaded
        st.sidebar.success(f"✅ {st.session_state.uploaded_filename} ready")

st.sidebar.markdown("---")
st.sidebar.markdown("### 📖 How to Use")
st.sidebar.markdown("""
**Option 1: Web/YouTube**
1. Enter a topic or YouTube URL
2. AI researches and generates post

**Option 2: PDF Document**
1. Upload PDF document (max 3MB)
2. Specify topic/angle from document
3. AI creates focused post
4. Ask multiple topics from same doc!

**Examples:**
- "AI trends in healthcare 2024"
- "https://youtube.com/watch?v=..."
- Upload PDF → "climate change impacts"

**Refinements:**
- "Make it more formal"
- "Remove the emojis"
- "Shorten to 200 words"
""")

# New Conversation button
if st.sidebar.button("🔄 New Conversation", use_container_width=True):
    # Clear backend conversation history if exists
    if st.session_state.conversation_id:
        try:
            httpx.delete(f"{API_URL}/api/conversation/{st.session_state.conversation_id}", timeout=5.0)
        except:
            pass  # Ignore errors, just clear frontend
    
    # Clear frontend state
    st.session_state.messages = []
    st.session_state.conversation_id = None
    st.session_state.uploaded_file_id = None
    st.session_state.uploaded_filename = None
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ System Status")
try:
    response = httpx.get(f"{API_URL}/", timeout=2.0)
    if response.status_code == 200:
        st.sidebar.success("✅ Backend Online")
    else:
        st.sidebar.error("❌ Backend Error")
except:
    st.sidebar.error("❌ Backend Offline")
    st.sidebar.code("uv run uvicorn backend.main:app --reload", language="bash")
