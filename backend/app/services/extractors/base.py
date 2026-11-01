from abc import ABC, abstractmethod
from typing import Dict, NamedTuple, Optional
from app.schemas.link import SiteType

class ExtractedMetadata(NamedTuple):
    title: str
    description: str
    site_type: SiteType
    image_url: Optional[str] = None
    price: Optional[str] = None
    specs: Optional[Dict[str, str]] = None

class BaseExtractor(ABC):
    @abstractmethod
    async def extract(self, url: str) -> ExtractedMetadata:
        pass
