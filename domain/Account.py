# coding: utf-8
from sqlalchemy import Column, DateTime, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class Account(Base):
    __tablename__ = 'account'

    id = Column(UUID, primary_key=True, server_default=text("gen_random_uuid()"))
    subjectId = Column(UUID)
    uid = Column(UUID)
    role = Column(String(255))
    nickName = Column(String(255))
    email = Column(String(255))
    activateTime = Column(DateTime(True), nullable=False)
    updateTime = Column(DateTime(True), nullable=False)
