import asyncio
import subprocess
from typing import AsyncGenerator
import re

async def stream_youtube_video(url: str) -> AsyncGenerator[bytes, None]:
    """
    Directly streams 720p YouTube video to client via yt-dlp stdout pipe.
    Zero permanent files are stored on server disk.
    """
    # yt-dlp command to stream best video format up to 720p directly to stdout
    cmd = [
        "yt-dlp",
        "--no-playlist",
        "-f", "best[height<=720]/best",
        "-o", "-",
        url,
    ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        while True:
            chunk = await process.stdout.read(64 * 1024)  # 64 KB chunks
            if not chunk:
                break
            yield chunk
    finally:
        if process.returncode is None:
            try:
                process.kill()
            except ProcessLookupError:
                pass

def get_safe_filename(title: str) -> str:
    cleaned = re.sub(r'[^a-zA-Z0-9_\- ]', '', title).strip().replace(' ', '_')
    if not cleaned:
        cleaned = "video"
    return f"{cleaned}_720p.mp4"
