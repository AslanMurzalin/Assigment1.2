from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from app.api.dependencies import get_link_service, get_current_user
from app.services.link_service import LinkService
from app.schemas.auth import UserRead
from app.schemas.link import LinkCreate, LinkUpdate, LinkRead

router = APIRouter(prefix="/links", tags=["Links"])

@router.get("", response_model=List[LinkRead])
async def list_links(
    q: Optional[str] = Query(None, description="Search term across title and user notes"),
    tag: Optional[str] = Query(None, description="Filter links by tag name"),
    current_user: UserRead = Depends(get_current_user),
    link_service: LinkService = Depends(get_link_service),
) -> List[LinkRead]:
    return await link_service.list_links(user_id=current_user.id, q=q, tag=tag)

@router.post("", response_model=LinkRead, status_code=status.HTTP_201_CREATED)
async def create_link(
    link_in: LinkCreate,
    current_user: UserRead = Depends(get_current_user),
    link_service: LinkService = Depends(get_link_service),
) -> LinkRead:
    return await link_service.create_link(user_id=current_user.id, link_in=link_in)

@router.get("/{id}", response_model=LinkRead)
async def get_link_by_id(
    id: str,
    current_user: UserRead = Depends(get_current_user),
    link_service: LinkService = Depends(get_link_service),
) -> LinkRead:
    return await link_service.get_link(user_id=current_user.id, link_id=id)

@router.patch("/{id}", response_model=LinkRead)
async def update_link(
    id: str,
    link_update: LinkUpdate,
    current_user: UserRead = Depends(get_current_user),
    link_service: LinkService = Depends(get_link_service),
) -> LinkRead:
    return await link_service.update_link(
        user_id=current_user.id,
        link_id=id,
        link_update=link_update,
    )

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_link(
    id: str,
    current_user: UserRead = Depends(get_current_user),
    link_service: LinkService = Depends(get_link_service),
) -> None:
    await link_service.delete_link(user_id=current_user.id, link_id=id)
