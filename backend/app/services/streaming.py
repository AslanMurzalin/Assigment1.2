import asyncio
import subprocess
import shutil
import sys
import os
from typing import AsyncGenerator
import re

def get_ytdlp_bin() -> str:
    venv_bin = os.path.join(os.path.dirname(sys.executable), "yt-dlp.exe" if sys.platform == "win32" else "yt-dlp")
    if os.path.exists(venv_bin):
        return venv_bin
    return shutil.which("yt-dlp") or "yt-dlp"

def get_ffmpeg_path() -> str | None:
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if os.path.exists(exe):
            return exe
    except Exception:
        pass
    return shutil.which("ffmpeg")

async def stream_youtube_video(url: str) -> AsyncGenerator[bytes, None]:
    """
    Directly streams 720p YouTube video to client via yt-dlp stdout pipe.
    Zero permanent files are stored on server disk.
    Uses thread-safe subprocess.Popen with asyncio.to_thread for universal
    compatibility across Windows and Unix event loops.
    """
    ytdlp_bin = get_ytdlp_bin()
    ffmpeg_exe = get_ffmpeg_path()

    cmd = [
        ytdlp_bin,
        "--no-playlist",
    ]

    if ffmpeg_exe:
        cmd.extend(["--ffmpeg-location", ffmpeg_exe])

    # Add node as JS runtime if available to prevent YouTube JS extraction deprecation errors
    if shutil.which("node"):
        cmd.extend(["--js-runtimes", "node"])

    # Robust format selection: best video <= 720p + best audio, fallback to combined best <= 720p, or best available
    cmd.extend([
        "-f", "bestvideo[height<=720]+bestaudio/best[height<=720]/bestvideo+bestaudio/best",
        "-o", "-",
        url,
    ])

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        bufsize=64 * 1024,
    )

    try:
        while True:
            # Read 64 KB chunk in worker thread to prevent event loop blocking
            chunk = await asyncio.to_thread(process.stdout.read, 64 * 1024)
            if not chunk:
                break
            yield chunk
    finally:
        if process.poll() is None:
            try:
                process.kill()
            except ProcessLookupError:
                pass
        if process.stdout:
            process.stdout.close()

def get_safe_filename(title: str) -> str:
    cleaned = re.sub(r'[^a-zA-Z0-9_\- ]', '', title).strip().replace(' ', '_')
    if not cleaned:
        cleaned = "video"
    return f"{cleaned}_720p.mp4"
