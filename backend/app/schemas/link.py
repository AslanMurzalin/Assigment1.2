from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class SiteType(str, Enum):
    youtube = "youtube"
    generic = "generic"

class LinkCreate(BaseModel):
    url: str
    user_notes: Optional[str] = ""
    tags: Optional[List[str]] = []

class LinkUpdate(BaseModel):
    user_notes: Optional[str] = None
    tags: Optional[List[str]] = None

class LinkRead(BaseModel):
    id: str
    user_id: str
    url: str
    title: str
    description: str
    site_type: SiteType
    user_notes: str
    tags: List[str]
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
