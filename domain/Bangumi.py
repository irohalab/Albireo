from sqlalchemy.dialects.postgresql import JSONB

from domain.Image import Image
from domain.User import User
from domain.base import Base
from domain.Episode import Episode
from domain.VideoFile import VideoFile
from sqlalchemy import Column, Integer, TEXT, DATE, TIMESTAMP, String, CheckConstraint, TEXT, Text, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime


class Bangumi(Base):
    __tablename__ = 'bangumi'
    __table_args__ = (
        CheckConstraint(
            '"subType" = ANY (ARRAY[\'other\'::text, \'TV\'::text, \'web\'::text, \'OVA\'::text, \'movie\'::text, \'Novel\'::text, \'Comic\'::text, \'Illustration\'::text, \'jp\'::text, \'en\'::text, \'cn\'::text, \'PC\'::text, \'NDS\'::text, \'PSP\'::text, \'PS2\'::text, \'PS3\'::text, \'Xbox360\'::text, \'Mac OS\'::text, \'PS5\'::text, \'Xbox Series X/S\'::text, \'PS4\'::text, \'Xbox One\'::text, \'Nintendo Switch\'::text, \'Wii U\'::text, \'Wii\'::text, \'PS Vita\'::text, \'3DS\'::text, \'iOS\'::text, \'Android\'::text, \'ARC\'::text, \'XBOX\'::text, \'GameCube\'::text, \'Dreamcast\'::text, \'Nitendo 64\'::text, \'PlayStation\'::text, \'SFC\'::text, \'FC\'::text, \'NEOGEO Pocket Color\'::text, \'GBA\'::text, \'GB\'::text, \'Virtual Boy\'::text, \'WonderSwan Color\'::text, \'WonderSwan\'::text])'),
    )

    id = Column(postgresql.UUID(as_uuid=True), primary_key=True, default=uuid4)
    bgm_id = Column(Integer, nullable=False, unique=True)
    name = Column(TEXT, nullable=False)
    name_cn = Column(TEXT, nullable=False)
    type = Column(Integer, nullable=False)
    eps = Column(Integer, nullable=False)
    summary = Column(TEXT, nullable=False)
    # The bangumi cover url from the bgm.tv
    image = Column(TEXT, nullable=False)
    air_date = Column(DATE, nullable=False)
    air_weekday = Column(Integer, nullable=False)
    # @deprecated
    rss = Column(TEXT, nullable=True)
    # dmhy search criteria
    # @deprecated
    dmhy = Column(TEXT, nullable=True)
    eps_no_offset = Column(Integer, nullable=True)
    # acg.rip search criteria
    acg_rip = Column(TEXT, nullable=True)
    # libyk.so search criteria, this field should be a JSON string contains two fields: {t: string, q: string}
    libyk_so = Column(TEXT, nullable=True)
    # bangumi.moe tag id array, this field should be a serialized JSON array contains strings
    bangumi_moe = Column(TEXT, nullable=True)
    # nyaa search query string. should already be urlencoded
    nyaa = Column(TEXT, nullable=True)
    # new scanner for dmhy and bangumi_moe
    universal = Column(TEXT, nullable=True)
    # @deprecated
    eps_regex = Column(TEXT, nullable=True)
    status = Column(Integer, nullable=False)
    create_time = Column(TIMESTAMP, default=datetime.now, nullable=False)
    update_time = Column(TIMESTAMP, default=datetime.now, nullable=False)

    # dominant color extracted from current bangumi cover image
    # @deprecated
    cover_color = Column(String, nullable=True)

    cover_image_id = Column(postgresql.UUID(as_uuid=True), nullable=True)

    # this mark is used by DeleteScanner to start a task for deleting certain bangumi and all data associated.
    # it is a date time when bangumi is schedule to delete
    delete_mark = Column(TIMESTAMP, nullable=True)

    created_by_uid = Column(postgresql.UUID(as_uuid=True), nullable=True)
    maintained_by_uid = Column(postgresql.UUID(as_uuid=True), nullable=True)

    # how many days exceed the airdate of its episode will make an alert to maintainer.
    alert_timeout = Column(Integer, default=2, nullable=False)

    item_id = Column(postgresql.UUID(as_uuid=True))
    subType = Column(TEXT)
    properties = Column(JSONB(astext_type=Text()), nullable=False, server_default=text("'{}'::jsonb"))

    # relationships
    episodes = relationship('Episode', order_by=Episode.episode_no, back_populates='bangumi',
                            cascade='all, delete, delete-orphan')

    favorite = relationship('Favorites', back_populates='bangumi', uselist=False)

    watch_progress_list = relationship('WatchProgress', back_populates='bangumi')

    video_files = relationship('VideoFile', order_by=VideoFile.bangumi_id, back_populates='bangumi',
                               cascade='all, delete, delete-orphan')

    cover_image = relationship(Image,
                               foreign_keys=[cover_image_id],
                               primaryjoin='Bangumi.cover_image_id==Image.id')

    created_by = relationship(User,
                              foreign_keys=[created_by_uid],
                              primaryjoin='Bangumi.created_by_uid==User.id')

    maintained_by = relationship(User,
                                 foreign_keys=[maintained_by_uid],
                                 primaryjoin='Bangumi.maintained_by_uid==User.id')

    # constant of bangumi status
    # A pending bangumi is not started to show on tv yet
    STATUS_PENDING = 0
    # An on air bangumi is currently on air on tv. And not finished yet
    STATUS_ON_AIR = 1
    # A finished bangumi will no longer need to scanned
    STATUS_FINISHED = 2

    # constant of bangumi type
    # anime type
    TYPE_ANIME = 2
    # japanese tv drama series type
    TYPE_JAPANESE_TV_DRAMA_SERIES = 6
