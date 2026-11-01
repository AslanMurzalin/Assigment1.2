from urllib.parse import urlparse
from app.services.extractors.base import BaseExtractor, ExtractedMetadata
from app.services.extractors.youtube import YouTubeExtractor
from app.services.extractors.generic import GenericExtractor
from app.services.extractors.marketplace import OzonExtractor, WildberriesExtractor, AliExpressExtractor


class MetadataExtractorService:
    def __init__(self):
        self.youtube_extractor = YouTubeExtractor()
        self.ozon_extractor = OzonExtractor()
        self.wb_extractor = WildberriesExtractor()
        self.aliexpress_extractor = AliExpressExtractor()
        self.generic_extractor = GenericExtractor()

    def is_youtube_url(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            host = parsed.netloc.lower()
            return "youtube.com" in host or "youtu.be" in host
        except Exception:
            return False

    def is_ozon_url(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            host = parsed.netloc.lower()
            return any(d in host for d in ["ozon.ru", "ozon.by", "ozon.kz"])
        except Exception:
            return False

    def is_wb_url(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            host = parsed.netloc.lower()
            return any(d in host for d in ["wildberries.ru", "wb.ru", "wildberries.by", "wildberries.kz"])
        except Exception:
            return False

    def is_aliexpress_url(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            host = parsed.netloc.lower()
            return any(d in host for d in ["aliexpress.com", "aliexpress.ru", "ali.express"])
        except Exception:
            return False

    async def extract(self, url: str) -> ExtractedMetadata:
        if self.is_youtube_url(url):
            return await self.youtube_extractor.extract(url)
        if self.is_ozon_url(url):
            return await self.ozon_extractor.extract(url)
        if self.is_wb_url(url):
            return await self.wb_extractor.extract(url)
        if self.is_aliexpress_url(url):
            return await self.aliexpress_extractor.extract(url)
        return await self.generic_extractor.extract(url)


metadata_extractor_service = MetadataExtractorService()
