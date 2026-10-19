from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from app.api.dependencies import get_link_service, get_current_user
from app.services.link_service import LinkService
from app.schemas.auth import UserRead
from app.schemas.link import SiteType
from app.services.streaming import stream_youtube_video, get_safe_filename

router = APIRouter(prefix="/links", tags=["Downloads"])

@router.get("/{id}/download")
async def download_video(
    id: str,
    current_user: UserRead = Depends(get_current_user),
    link_service: LinkService = Depends(get_link_service),
):
    link = await link_service.get_link(user_id=current_user.id, link_id=id)

    if link.site_type != SiteType.youtube:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Direct video streaming is only supported for YouTube links",
        )

    filename = get_safe_filename(link.title)
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Cache-Control": "no-cache",
    }

    return StreamingResponse(
        stream_youtube_video(link.url),
        media_type="video/mp4",
        headers=headers,
    )
