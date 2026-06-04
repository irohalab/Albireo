from domain.base import Base
from sqlalchemy import Column, TEXT, String, Integer
from sqlalchemy.dialects import postgresql
from uuid import uuid4


class Image(Base):
    __tablename__ = 'image'

    id = Column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4)
    file_path = Column(TEXT, nullable=True)
    dominant_color = Column(String, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    url = Column(TEXT, nullable=True)
