import asyncio
import subprocess
import shutil
import sys
import os
import tempfile
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
    Downloads 720p YouTube video to a temp file, then streams it to client.
    Temp file is deleted immediately after streaming completes.

    Using a temp file instead of piping stdout allows yt-dlp to:
      - Download video + audio streams concurrently (much faster)
      - Produce a proper MP4 with duration metadata (no fragmented/live issues)
      - Use its full optimization pipeline without pipe throughput limits

    Zero permanent files are stored on server disk.
    """
    ytdlp_bin = get_ytdlp_bin()
    ffmpeg_exe = get_ffmpeg_path()

    # Create isolated temp directory for yt-dlp output
    tmp_dir = tempfile.mkdtemp()
    tmp_path = os.path.join(tmp_dir, "video.mp4")

    try:
        cmd = [
            ytdlp_bin,
            "--no-playlist",
            "--force-overwrites",
        ]

        if ffmpeg_exe:
            cmd.extend(["--ffmpeg-location", ffmpeg_exe])

        # Add node as JS runtime if available to prevent YouTube JS extraction deprecation errors
        if shutil.which("node"):
            cmd.extend(["--js-runtimes", "node"])

        # Robust format selection prioritizing H.264 (avc1) for fastest muxing:
        #   1. Best H.264 video ≤720p + best AAC audio  (fastest mux, best compat)
        #   2. Best any-codec video ≤720p + best audio   (fallback, may use VP9/AV1)
        #   3. Best pre-muxed ≤720p                      (progressive, no mux needed)
        #   4. Absolute fallback
        cmd.extend([
            "-f", (
                "bestvideo[height<=720][vcodec^=avc1]+bestaudio[acodec^=mp4a]/"
                "bestvideo[height<=720]+bestaudio/"
                "best[height<=720]/"
                "bestvideo+bestaudio/best"
            ),
            "--merge-output-format", "mp4",
            "--no-part",
            "-o", tmp_path,
            url,
        ])

        # Run yt-dlp in a worker thread (blocks until download + merge completes)
        process = await asyncio.to_thread(
            subprocess.run,
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        if process.returncode != 0 or not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
            raise RuntimeError("yt-dlp failed to download the video")

        # Stream the completed file to client in chunks
        chunk_size = 256 * 1024  # 256 KB chunks

        with open(tmp_path, "rb") as f:
            while True:
                chunk = await asyncio.to_thread(f.read, chunk_size)
                if not chunk:
                    break
                yield chunk
    finally:
        # Always clean up temp directory and all contents
        try:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        except OSError:
            pass


def get_file_size(url: str) -> int | None:
    """Pre-check: get the temp file size after download for Content-Length header."""
    return None  # Size unknown until download completes; handled by router


def get_safe_filename(title: str) -> str:
    cleaned = re.sub(r'[^a-zA-Z0-9_\- ]', '', title).strip().replace(' ', '_')
    if not cleaned:
        cleaned = "video"
    return f"{cleaned}_720p.mp4"
