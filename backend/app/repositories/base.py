from abc import ABC, abstractmethod
from typing import List, Optional
from app.schemas.link import LinkRead, SiteType
from app.schemas.auth import UserRead

class AbstractUserRepository(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[UserRead]:
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[dict]:
        """Returns user dict including hashed_password for auth verification."""
        pass

    @abstractmethod
    async def create(self, email: str, hashed_password: str) -> UserRead:
        pass


class AbstractLinkRepository(ABC):
    @abstractmethod
    async def create(
        self,
        user_id: str,
        url: str,
        title: str,
        description: str,
        site_type: SiteType,
        user_notes: str,
        tags: List[str],
    ) -> LinkRead:
        pass

    @abstractmethod
    async def get_by_id(self, link_id: str) -> Optional[LinkRead]:
        pass

    @abstractmethod
    async def list_by_user(
        self,
        user_id: str,
        q: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> List[LinkRead]:
        pass

    @abstractmethod
    async def update(
        self,
        link_id: str,
        user_notes: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Optional[LinkRead]:
        pass

    @abstractmethod
    async def delete(self, link_id: str) -> bool:
        pass
