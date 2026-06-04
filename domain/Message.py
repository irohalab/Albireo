# coding: utf-8
from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()
metadata = Base.metadata


class Message(Base):
    __tablename__ = 'message'
    __table_args__ = (
        CheckConstraint('"contentType" = ANY (ARRAY[\'text\'::text, \'html\'::text, \'markdown\'::text])'),
        CheckConstraint('"threadType" = ANY (ARRAY[\'Ticket\'::text, \'Message\'::text])')
    )

    id = Column(UUID, primary_key=True, server_default=text("gen_random_uuid()"))
    threadId = Column(String(255))
    threadTitle = Column(String(255))
    threadType = Column(Text, nullable=False, server_default=text("'Message'::text"))
    content = Column(Text, nullable=False)
    contentType = Column(Text, nullable=False, server_default=text("'text'::text"))
    renderedContent = Column(Text)
    read = Column(Boolean, nullable=False, server_default=text("false"))
    createdTime = Column(DateTime(True), nullable=False)
    updatedTime = Column(DateTime(True))
    recipient = Column(ForeignKey(u'account.id'))
    sender = Column(ForeignKey(u'account.id'))

    account = relationship(u'Account', primaryjoin='Message.recipient == Account.id')
    account1 = relationship(u'Account', primaryjoin='Message.sender == Account.id')

