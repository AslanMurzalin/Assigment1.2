from urllib.parse import urlparse
from app.services.extractors.base import BaseExtractor, ExtractedMetadata
from app.services.extractors.youtube import YouTubeExtractor
from app.services.extractors.generic import GenericExtractor

class MetadataExtractorService:
    def __init__(self):
        self.youtube_extractor = YouTubeExtractor()
        self.generic_extractor = GenericExtractor()

    def is_youtube_url(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            host = parsed.netloc.lower()
            return "youtube.com" in host or "youtu.be" in host
        except Exception:
            return False

    async def extract(self, url: str) -> ExtractedMetadata:
        if self.is_youtube_url(url):
            return await self.youtube_extractor.extract(url)
        return await self.generic_extractor.extract(url)

metadata_extractor_service = MetadataExtractorService()
