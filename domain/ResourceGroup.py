# coding: utf-8
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from domain.base import Base


class ResourceGroup(Base):
    __tablename__ = 'resource_group'

    id = Column(UUID, primary_key=True, server_default=text("gen_random_uuid()"))
    displayName = Column(String(255), nullable=False)
    createdTime = Column(DateTime(True), nullable=False)
    updatedTime = Column(DateTime(True))
    lastCheckTime = Column(DateTime(True))
    alertThresholdDay = Column(Integer, nullable=False, server_default=text("2"))
    bangumi = Column(ForeignKey(u'bangumi.id', ondelete=u'CASCADE'), nullable=False)
    scanner = Column(JSONB(astext_type=Text()), nullable=False)
    color = Column(String(255))

    bangumi1 = relationship(u'Bangumi')
    video_files = relationship(u'VideoFile', back_populates='resource_group')
