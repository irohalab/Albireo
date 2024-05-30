from domain.Image import Image
from domain.base import Base
from domain.TorrentFile import TorrentFile
from domain.VideoFile import VideoFile
from sqlalchemy import Column, Integer, TEXT, DATE, ForeignKey, String, TIMESTAMP
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime


class Episode(Base):
    __tablename__ = 'episodes'

    id = Column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4)
    bangumi_id = Column(postgresql.UUID(as_uuid=True), ForeignKey('bangumi.id'), nullable=False)
    bgm_eps_id = Column(Integer, nullable=False)
    episode_no = Column(Integer, nullable=False)
    name = Column(TEXT, nullable=True)
    name_cn = Column(TEXT, nullable=True)
    duration = Column(String, nullable=True)
    airdate = Column(DATE, nullable=True)
    status = Column(Integer, nullable=False)
    create_time = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    update_time = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)

    delete_mark = Column(TIMESTAMP, nullable=True)

    # dominant color extracted from thumbnail image
    # @deprecated
    thumbnail_color = Column(String, nullable=True)

    thumbnail_image_id = Column(postgresql.UUID(as_uuid=True), nullable=True)

    bangumi = relationship('Bangumi', back_populates='episodes')

    torrent_files = relationship('TorrentFile', order_by=TorrentFile.episode_id, back_populates='episode',
                                 cascade='all, delete, delete-orphan')

    video_files = relationship('VideoFile', order_by=VideoFile.episode_id, back_populates='episode',
                               cascade='all, delete, delete-orphan')

    watch_progress = relationship('WatchProgress', uselist=False, back_populates='episode')

    thumbnail_image = relationship(Image,
                                   foreign_keys=[thumbnail_image_id],
                                   primaryjoin='Episode.thumbnail_image_id==Image.id')

    STATUS_NOT_DOWNLOADED = 0
    STATUS_DOWNLOADING = 1
    STATUS_DOWNLOADED = 2

    def is_blob_storage_url_v0(self):
        return self.video_files and self.video_files[0].blob_storage_url_v0 is not None
