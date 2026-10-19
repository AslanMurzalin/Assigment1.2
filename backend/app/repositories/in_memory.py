import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from app.repositories.base import AbstractUserRepository, AbstractLinkRepository
from app.schemas.auth import UserRead
from app.schemas.link import LinkRead, SiteType

class InMemoryUserRepository(AbstractUserRepository):
    def __init__(self):
        # Maps user_id -> dict with user data including hashed_password
        self._users: Dict[str, dict] = {}
        # Maps email -> user_id for uniqueness check
        self._emails: Dict[str, str] = {}

    async def get_by_id(self, user_id: str) -> Optional[UserRead]:
        user_data = self._users.get(user_id)
        if not user_data:
            return None
        return UserRead(
            id=user_data["id"],
            email=user_data["email"],
            created_at=user_data["created_at"],
        )

    async def get_by_email(self, email: str) -> Optional[dict]:
        user_id = self._emails.get(email.strip().lower())
        if not user_id:
            return None
        return self._users.get(user_id)

    async def create(self, email: str, hashed_password: str) -> UserRead:
        normalized_email = email.strip().lower()
        if normalized_email in self._emails:
            raise ValueError("Email already registered")

        user_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        record = {
            "id": user_id,
            "email": normalized_email,
            "hashed_password": hashed_password,
            "created_at": now,
        }
        self._users[user_id] = record
        self._emails[normalized_email] = user_id

        return UserRead(
            id=user_id,
            email=normalized_email,
            created_at=now,
        )


class InMemoryLinkRepository(AbstractLinkRepository):
    def __init__(self):
        self._links: Dict[str, dict] = {}

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
        link_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        record = {
            "id": link_id,
            "user_id": user_id,
            "url": url,
            "title": title,
            "description": description,
            "site_type": site_type,
            "user_notes": user_notes,
            "tags": [t.strip().lower() for t in tags if t.strip()],
            "created_at": now,
            "updated_at": None,
        }
        self._links[link_id] = record
        return LinkRead(**record)

    async def get_by_id(self, link_id: str) -> Optional[LinkRead]:
        record = self._links.get(link_id)
        if not record:
            return None
        return LinkRead(**record)

    async def list_by_user(
        self,
        user_id: str,
        q: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> List[LinkRead]:
        results = [l for l in self._links.values() if l["user_id"] == user_id]

        if q and q.strip():
            query = q.strip().lower()
            results = [
                l for l in results
                if query in l["title"].lower() or query in l["user_notes"].lower()
            ]

        if tag and tag.strip():
            filter_tag = tag.strip().lower()
            results = [
                l for l in results
                if any(t.lower() == filter_tag for t in l["tags"])
            ]

        results.sort(key=lambda x: x["created_at"], reverse=True)
        return [LinkRead(**r) for r in results]

    async def update(
        self,
        link_id: str,
        user_notes: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Optional[LinkRead]:
        record = self._links.get(link_id)
        if not record:
            return None

        if user_notes is not None:
            record["user_notes"] = user_notes.strip()
        if tags is not None:
            record["tags"] = [t.strip().lower() for t in tags if t.strip()]

        record["updated_at"] = datetime.now(timezone.utc)
        return LinkRead(**record)

    async def delete(self, link_id: str) -> bool:
        if link_id in self._links:
            del self._links[link_id]
            return True
        return False
