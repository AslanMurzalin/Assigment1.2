from sqlalchemy import Column, String, Table, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base

# Many-to-Many junction table: link_tags
link_tags = Table(
    "link_tags",
    Base.metadata,
    Column("link_id", String, ForeignKey("links.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", String, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

class TagModel(Base):
    __tablename__ = "tags"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
