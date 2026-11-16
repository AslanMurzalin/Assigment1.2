import time
from urllib.parse import urlparse
from app.services.extractors.base import BaseExtractor, ExtractedMetadata
from app.services.extractors.youtube import YouTubeExtractor
from app.services.extractors.generic import GenericExtractor
from app.services.extractors.marketplace import OzonExtractor, WildberriesExtractor, AliExpressExtractor
from app.core.telemetry import EXTRACTION_DURATION_SECONDS, EXTRACTION_FAILURES_TOTAL


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
        extractor_type = "generic"
        if self.is_youtube_url(url):
            extractor = self.youtube_extractor
            extractor_type = "youtube"
        elif self.is_ozon_url(url):
            extractor = self.ozon_extractor
            extractor_type = "ozon"
        elif self.is_wb_url(url):
            extractor = self.wb_extractor
            extractor_type = "wildberries"
        elif self.is_aliexpress_url(url):
            extractor = self.aliexpress_extractor
            extractor_type = "aliexpress"
        else:
            extractor = self.generic_extractor
            extractor_type = "generic"

        start_time = time.time()
        try:
            result = await extractor.extract(url)
            duration = time.time() - start_time
            EXTRACTION_DURATION_SECONDS.labels(extractor_type=extractor_type).observe(duration)
            return result
        except Exception as e:
            EXTRACTION_FAILURES_TOTAL.labels(
                extractor_type=extractor_type,
                error_type=type(e).__name__,
            ).inc()
            raise


metadata_extractor_service = MetadataExtractorService()
