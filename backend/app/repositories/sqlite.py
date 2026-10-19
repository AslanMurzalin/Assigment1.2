import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.repositories.base import AbstractUserRepository, AbstractLinkRepository
from app.models.user import UserModel
from app.models.tag import TagModel
from app.models.link import LinkModel
from app.schemas.auth import UserRead
from app.schemas.link import LinkRead, SiteType

class SQLiteUserRepository(AbstractUserRepository):
    def __init__(self, db: Session):
        self.db = db

    async def get_by_id(self, user_id: str) -> Optional[UserRead]:
        user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            return None
        return UserRead(
            id=user.id,
            email=user.email,
            created_at=user.created_at,
        )

    async def get_by_email(self, email: str) -> Optional[dict]:
        user = self.db.query(UserModel).filter(UserModel.email == email.strip().lower()).first()
        if not user:
            return None
        return {
            "id": user.id,
            "email": user.email,
            "hashed_password": user.hashed_password,
            "created_at": user.created_at,
        }

    async def create(self, email: str, hashed_password: str) -> UserRead:
        normalized_email = email.strip().lower()
        new_user = UserModel(
            id=str(uuid.uuid4()),
            email=normalized_email,
            hashed_password=hashed_password,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)

        return UserRead(
            id=new_user.id,
            email=new_user.email,
            created_at=new_user.created_at,
        )


class SQLiteLinkRepository(AbstractLinkRepository):
    def __init__(self, db: Session):
        self.db = db

    def _get_or_create_tags(self, tag_names: List[str]) -> List[TagModel]:
        tag_models = []
        for raw_name in tag_names:
            clean_name = raw_name.strip().lower().replace("#", "")
            if not clean_name:
                continue
            existing = self.db.query(TagModel).filter(TagModel.name == clean_name).first()
            if existing:
                tag_models.append(existing)
            else:
                new_tag = TagModel(id=str(uuid.uuid4()), name=clean_name)
                self.db.add(new_tag)
                self.db.flush()
                tag_models.append(new_tag)
        return tag_models

    def _to_schema(self, model: LinkModel) -> LinkRead:
        return LinkRead(
            id=model.id,
            user_id=model.user_id,
            url=model.url,
            title=model.title,
            description=model.description,
            site_type=SiteType(model.site_type),
            user_notes=model.user_notes,
            tags=[t.name for t in model.tags],
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

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
        tag_models = self._get_or_create_tags(tags)
        new_link = LinkModel(
            id=str(uuid.uuid4()),
            user_id=user_id,
            url=url,
            title=title,
            description=description,
            site_type=site_type.value,
            user_notes=user_notes,
            tags=tag_models,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(new_link)
        self.db.commit()
        self.db.refresh(new_link)
        return self._to_schema(new_link)

    async def get_by_id(self, link_id: str) -> Optional[LinkRead]:
        model = self.db.query(LinkModel).filter(LinkModel.id == link_id).first()
        if not model:
            return None
        return self._to_schema(model)

    async def list_by_user(
        self,
        user_id: str,
        q: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> List[LinkRead]:
        query = self.db.query(LinkModel).filter(LinkModel.user_id == user_id)

        if q and q.strip():
            term = f"%{q.strip().lower()}%"
            query = query.filter(
                or_(
                    LinkModel.title.ilike(term),
                    LinkModel.user_notes.ilike(term),
                )
            )

        if tag and tag.strip():
            clean_tag = tag.strip().lower().replace("#", "")
            query = query.filter(LinkModel.tags.any(TagModel.name == clean_tag))

        query = query.order_by(LinkModel.created_at.desc())
        models = query.all()
        return [self._to_schema(m) for m in models]

    async def update(
        self,
        link_id: str,
        user_notes: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Optional[LinkRead]:
        model = self.db.query(LinkModel).filter(LinkModel.id == link_id).first()
        if not model:
            return None

        if user_notes is not None:
            model.user_notes = user_notes.strip()

        if tags is not None:
            model.tags = self._get_or_create_tags(tags)

        model.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(model)
        return self._to_schema(model)

    async def delete(self, link_id: str) -> bool:
        model = self.db.query(LinkModel).filter(LinkModel.id == link_id).first()
        if not model:
            return False
        self.db.delete(model)
        self.db.commit()
        return True
