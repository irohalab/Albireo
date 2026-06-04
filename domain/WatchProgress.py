from domain.base import Base
from sqlalchemy import Column, Integer, TIMESTAMP, ForeignKey, Float
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime


class WatchProgress(Base):
    __tablename__ = 'watch_progress'

    id = Column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(postgresql.UUID(as_uuid=True), nullable=False)
    bangumi_id = Column(postgresql.UUID(as_uuid=True), ForeignKey('bangumi.id'), nullable=False)
    episode_id = Column(postgresql.UUID(as_uuid=True), ForeignKey('episodes.id'), nullable=False)

    watch_status = Column(Integer, nullable=False)

    # last watched position in seconds, only usable when watch_status is WATCHING
    last_watch_position = Column(Float, nullable=True)

    last_watch_time = Column(TIMESTAMP, nullable=True)

    percentage = Column(Float, nullable=True)

    subItemId = Column(postgresql.UUID(as_uuid=True), nullable=True)
    externalSubItemFavoriteId = Column(postgresql.UUID(as_uuid=True), nullable=True)

    bangumi = relationship('Bangumi', uselist=False, back_populates='watch_progress_list')

    episode = relationship('Episode', uselist=False, back_populates='watch_progress')

    # status is for favorites purpose
    WISH = 1
    WATCHED = 2
    WATCHING = 3
    PAUSE = 4
    ABANDONED = 5
