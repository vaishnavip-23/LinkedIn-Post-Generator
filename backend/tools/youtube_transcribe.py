"""
YouTube Transcription Tool - Local Whisper Integration

Downloads audio from YouTube videos using yt-dlp and transcribes
using local Whisper model. Enforces 15-minute duration limit.

Uses OpenAI Agents SDK @function_tool decorator.
"""

import os
import certifi

import yt_dlp
from openai import OpenAI
from agents import function_tool
from pydantic import ValidationError

from backend.models.schema import YouTubeContent


MAX_DURATION_SECONDS = 900  # 15 minutes

# Use certifi's certificate bundle for SSL verification
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()


@function_tool
async def youtube_transcribe(video_url: str) -> YouTubeContent:
    """Transcribe and analyze a YouTube video using local Whisper model.
    
    Use this when user provides a YouTube URL or asks to analyze/summarize a video.
    Downloads audio with yt-dlp, transcribes with local Whisper model.
    Maximum video length: 15 minutes.
    
    Args:
        video_url: The YouTube video URL (youtube.com or youtu.be format)
        
    Returns:
        YouTubeContent object with video metadata and transcript
    """
    # Get metadata once (no download)
    ydl_opts = {'quiet': True, 'no_warnings': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
    
    duration = info.get('duration', 0)
    
    # Check duration limits
    if duration <= 0:
        raise ValueError("Unable to determine video duration. Please check the URL.")
    
    if duration > MAX_DURATION_SECONDS:
        minutes = duration // 60
        raise ValueError(
            f"❌ Video is too long ({minutes} minutes). "
            f"Maximum allowed is 15 minutes. Please provide a shorter video."
        )
    
    title = info.get('title')
    if not title:
        raise ValueError("Video metadata missing title")
    
    # Download audio
    audio_path = "audio_file.mp3"
    download_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'audio_file',
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(download_opts) as ydl:
            ydl.download([video_url])
        
        # Transcribe with OpenAI Whisper API (much faster than local)
        openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        with open(audio_path, "rb") as audio_file:
            transcription = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        transcript = transcription.text.strip()
        
        if not transcript:
            raise ValueError("Transcription produced empty text")
        
        # Validate with Pydantic schema
        youtube_content = YouTubeContent.model_validate({
            "video_url": video_url,
            "title": title,
            "author": info.get('uploader') or info.get('channel'),
            "duration_seconds": duration,
            "transcript": transcript,
        })
        
        return youtube_content
        
    except ValidationError as exc:
        raise ValueError(f"Invalid YouTube content: {exc}") from exc
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)
