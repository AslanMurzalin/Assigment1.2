from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.base import AbstractUserRepository, AbstractLinkRepository
from app.repositories.sqlite import SQLiteUserRepository, SQLiteLinkRepository
from app.services.auth_service import AuthService
from app.services.link_service import LinkService
from app.services.extractors.dispatcher import metadata_extractor_service
from app.schemas.auth import UserRead

security_bearer = HTTPBearer(auto_error=False)

def get_user_repository(db: Session = Depends(get_db)) -> AbstractUserRepository:
    return SQLiteUserRepository(db)

def get_link_repository(db: Session = Depends(get_db)) -> AbstractLinkRepository:
    return SQLiteLinkRepository(db)

def get_auth_service(
    user_repo: AbstractUserRepository = Depends(get_user_repository),
) -> AuthService:
    return AuthService(user_repo)

def get_link_service(
    link_repo: AbstractLinkRepository = Depends(get_link_repository),
) -> LinkService:
    return LinkService(link_repo, metadata_extractor_service)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_bearer),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserRead:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return await auth_service.get_user_from_token(credentials.credentials)
