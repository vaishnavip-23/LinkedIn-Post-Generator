"""
YouTube Transcription Tool - Whisper API Integration

Downloads audio from YouTube videos using yt-dlp and transcribes
using OpenAI's Whisper API. Enforces 15-minute duration limit.

Decorated with @tool for automatic registration with the AI agent.
"""

import os
import re
import tempfile

import yt_dlp
from openai import OpenAI

from backend.models.schema import YouTubeContent
from backend.tools.registry import tool


MAX_DURATION_SECONDS = 900  # 15 minutes


@tool(
    name="youtube_transcribe",
    description="Transcribe and analyze a YouTube video using Whisper API. Use this when user provides a YouTube URL or asks to analyze/summarize a video. Maximum video length: 15 minutes.",
    parameters={
        "type": "object",
        "properties": {
            "video_url": {
                "type": "string",
                "description": "The YouTube video URL (youtube.com or youtu.be format)"
            }
        },
        "required": ["video_url"]
    }
)
async def youtube_transcribe(video_url: str) -> dict:
    """
    Transcribe a YouTube video with Whisper API.
    
    Args:
        video_url: YouTube video URL
        
    Returns:
        Dictionary with success status and formatted transcript
    """
    try:
        # Validate URL and get metadata
        video_id = _extract_video_id(video_url)
        metadata = _get_video_metadata(video_url)
        
        # Check duration limit
        duration = metadata['duration']
        if duration > MAX_DURATION_SECONDS:
            return {
                "success": False,
                "error": f"Video too long ({duration}s). Maximum: {MAX_DURATION_SECONDS}s (15 minutes)",
                "data": ""
            }
        
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {
                "success": False,
                "error": "OPENAI_API_KEY not configured",
                "data": ""
            }
        
        client = OpenAI(api_key=api_key)
        
        # Download and transcribe
        with tempfile.TemporaryDirectory() as temp_dir:
            audio_path = os.path.join(temp_dir, f"audio_{video_id}")
            
            # Download audio
            audio_file = _download_audio(video_url, audio_path)
            
            # Transcribe with Whisper
            transcript = _transcribe_audio(client, audio_file)
            
            # Create structured result
            youtube_content = YouTubeContent(
                video_url=video_url,
                title=metadata['title'],
                author=metadata.get('author'),
                duration_seconds=duration,
                transcript=transcript
            )
            
            # Format for post generation
            formatted_data = _format_youtube_content(youtube_content)
            
            return {
                "success": True,
                "tool_name": "youtube_transcribe",
                "data": formatted_data
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data": ""
        }


def _extract_video_id(url: str) -> str:
    """Extract video ID from YouTube URL."""
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'^([0-9A-Za-z_-]{11})$'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    raise ValueError(f"Invalid YouTube URL: {url}")


def _get_video_metadata(url: str) -> dict:
    """Get video metadata without downloading."""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            'title': info.get('title', 'Unknown'),
            'duration': info.get('duration', 0),
            'author': info.get('uploader', info.get('channel', 'Unknown'))
        }


def _download_audio(url: str, output_path: str) -> str:
    """Download audio from YouTube using yt-dlp."""
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
    return f"{output_path}.mp3"


def _transcribe_audio(client: OpenAI, audio_path: str) -> str:
    """Transcribe audio file using Whisper API."""
    with open(audio_path, 'rb') as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text"
        )
    return transcript


def _format_youtube_content(content: YouTubeContent) -> str:
    """Format YouTube content for LinkedIn post generation."""
    return (
        f"Video Title: {content.title}\n"
        f"Channel: {content.author}\n"
        f"Duration: {content.duration_seconds // 60} minutes\n"
        f"URL: {content.video_url}\n\n"
        f"Transcript:\n{content.transcript}"
    )
