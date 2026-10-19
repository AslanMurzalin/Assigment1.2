from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.tag import link_tags

class LinkModel(Base):
    __tablename__ = "links"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, default="", nullable=False)
    site_type = Column(String, default="generic", nullable=False)
    user_notes = Column(Text, default="", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = Column(DateTime, nullable=True)

    user = relationship("UserModel", back_populates="links")
    tags = relationship("TagModel", secondary=link_tags, backref="links", lazy="joined")
