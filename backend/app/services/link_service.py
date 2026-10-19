from typing import List, Optional
from fastapi import HTTPException, status
from app.repositories.base import AbstractLinkRepository
from app.schemas.link import LinkCreate, LinkUpdate, LinkRead
from app.services.extractors.dispatcher import MetadataExtractorService

class LinkService:
    def __init__(self, link_repo: AbstractLinkRepository, extractor: MetadataExtractorService):
        self.link_repo = link_repo
        self.extractor = extractor

    async def create_link(self, user_id: str, link_in: LinkCreate) -> LinkRead:
        url_str = str(link_in.url).strip()
        if not (url_str.startswith("http://") or url_str.startswith("https://")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="URL must start with http:// or https://",
            )

        # Extract metadata automatically
        metadata = await self.extractor.extract(url_str)

        return await self.link_repo.create(
            user_id=user_id,
            url=url_str,
            title=metadata.title,
            description=metadata.description,
            site_type=metadata.site_type,
            user_notes=link_in.user_notes or "",
            tags=link_in.tags or [],
        )

    async def list_links(
        self,
        user_id: str,
        q: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> List[LinkRead]:
        return await self.link_repo.list_by_user(user_id=user_id, q=q, tag=tag)

    async def get_link(self, user_id: str, link_id: str) -> LinkRead:
        link = await self.link_repo.get_by_id(link_id)
        if not link or link.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Link not found",
            )
        return link

    async def update_link(self, user_id: str, link_id: str, link_update: LinkUpdate) -> LinkRead:
        link = await self.get_link(user_id, link_id)
        updated = await self.link_repo.update(
            link_id=link.id,
            user_notes=link_update.user_notes,
            tags=link_update.tags,
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Link not found",
            )
        return updated

    async def delete_link(self, user_id: str, link_id: str) -> None:
        await self.get_link(user_id, link_id)
        deleted = await self.link_repo.delete(link_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Link not found",
            )
