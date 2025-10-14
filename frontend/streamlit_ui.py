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

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


async def generate_linkedin_post(query: str) -> Optional[dict]:
    """Call backend API to generate LinkedIn post from query."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{API_URL}/api/generate-linkedin-post",
                json={"query": query}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            st.error(f"API Error: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            st.error(f"Connection Error: {str(e)}")
            return None


def format_post_output(post_data: dict) -> str:
    """Format LinkedIn post with hashtags for display."""
    post = post_data["post"]
    content = post["content"]
    hashtags = post.get("hashtags", [])
    
    if hashtags:
        hashtag_str = " ".join(f"#{tag}" for tag in hashtags)
        return f"{content}\n\n{hashtag_str}"
    
    return content


if prompt := st.chat_input("Enter a topic to research and generate a LinkedIn post"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("🔍 Researching topic and generating LinkedIn post..."):
            result = asyncio.run(generate_linkedin_post(prompt))
            
            if result:
                linkedin_post = format_post_output(result)
                st.markdown(linkedin_post)
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": linkedin_post
                })
                
                st.success("✅ Post generated successfully!")
                
                with st.expander("📋 Copy to Clipboard"):
                    st.code(linkedin_post, language=None)
            else:
                error_msg = "Failed to generate post. Please try again."
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })

st.sidebar.markdown("### 📖 How to Use")
st.sidebar.markdown("""
1. Enter any topic in the chat
2. AI researches using Tavily + Exa
3. Receive ready-to-post LinkedIn content

**Example Topics:**
- "AI trends in healthcare 2024"
- "Remote team productivity strategies"
- "Sustainable business innovations"
""")

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
    st.sidebar.code("uv run uvicorn backend.api:app --reload", language="bash")
