from abc import ABC, abstractmethod
from typing import NamedTuple
from app.schemas.link import SiteType

class ExtractedMetadata(NamedTuple):
    title: str
    description: str
    site_type: SiteType

class BaseExtractor(ABC):
    @abstractmethod
    async def extract(self, url: str) -> ExtractedMetadata:
        pass
