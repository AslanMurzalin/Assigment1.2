import asyncio
import httpx
from urllib.parse import urlparse
from app.schemas.link import SiteType
from app.services.extractors.base import BaseExtractor, ExtractedMetadata

class YouTubeExtractor(BaseExtractor):
    async def extract(self, url: str) -> ExtractedMetadata:
        title = "YouTube Video"
        description = "YouTube video ready for 720p streaming."

        # Fast official oEmbed lookup first
        try:
            oembed_url = f"https://www.youtube.com/oembed?url={url}&format=json"
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.get(oembed_url)
                if resp.status_code == 200:
                    data = resp.json()
                    title = data.get("title", title)
                    author = data.get("author_name", "")
                    if author:
                        description = f"Uploaded by {author}. YouTube 720p stream available."
                    return ExtractedMetadata(title=title, description=description, site_type=SiteType.youtube)
        except Exception:
            pass

        # Fallback to yt-dlp metadata extraction
        try:
            loop = asyncio.get_event_loop()
            def run_yt_dlp():
                import yt_dlp
                ydl_opts = {'quiet': True, 'skip_download': True, 'extract_flat': True}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    return info.get('title'), info.get('description')

            yt_title, yt_desc = await loop.run_in_executor(None, run_yt_dlp)
            if yt_title:
                title = yt_title
            if yt_desc:
                description = yt_desc[:250] + ("..." if len(yt_desc) > 250 else "")
        except Exception:
            parsed = urlparse(url)
            title = f"YouTube ({parsed.path.replace('/', '')})"

        return ExtractedMetadata(title=title, description=description, site_type=SiteType.youtube)
