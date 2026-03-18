from __future__ import annotations
from datetime import datetime, date
from typing import List, Optional
from sqlalchemy import (
    Integer, String, DateTime, ForeignKey,
    Date, Text, Boolean, UniqueConstraint, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from mysite.database.db import Base


class ChatRoom(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(Integer, unique=True)
    group_name: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    members: Mapped[List["Member"]] = relationship(back_populates="room", cascade="all, delete-orphan",
                                                   lazy="selectin")
    messages: Mapped[List["Message"]] = relationship(back_populates="room", cascade="all, delete-orphan",
                                                     lazy="selectin")
    read_states: Mapped[List["ReadState"]] = relationship(back_populates="room", cascade="all, delete-orphan",
                                                          lazy="selectin")

    __table_args__ = (Index("ix_rooms_group_id", "group_id"),)


class Member(Base):
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"))
    email: Mapped[str] = mapped_column(String(200))
    full_name: Mapped[str] = mapped_column(String(200))
    is_teacher: Mapped[bool] = mapped_column(Boolean, default=False)
    is_online: Mapped[bool] = mapped_column(Boolean, default=False)
    joined_at: Mapped[date] = mapped_column(Date, default=date.today)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    room: Mapped["ChatRoom"] = relationship(back_populates="members")

    __table_args__ = (
        UniqueConstraint("room_id", "email", name="uq_members_room_email"),
        Index("ix_members_room_email", "room_id", "email"),
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"))
    sender_email: Mapped[str] = mapped_column(String(200))
    sender_name: Mapped[str] = mapped_column(String(200))
    is_teacher: Mapped[bool] = mapped_column(Boolean, default=False)
    text: Mapped[str] = mapped_column(Text, default="")
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    edited_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    room: Mapped["ChatRoom"] = relationship(back_populates="messages")
    attachments: Mapped[List["Attachment"]] = relationship(back_populates="message", cascade="all, delete-orphan",
                                                           lazy="selectin")

    __table_args__ = (
        Index("ix_messages_room_created", "room_id", "created_at"),
        Index("ix_messages_sender", "sender_email"),
    )


class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"))
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"))
    file_type: Mapped[str] = mapped_column(String(20))
    file_url: Mapped[str] = mapped_column(Text)
    file_name: Mapped[str] = mapped_column(String(200))
    mime_type: Mapped[str] = mapped_column(String(100))
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    duration_sec: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    message: Mapped["Message"] = relationship(back_populates="attachments")

    __table_args__ = (
        Index("ix_attachments_message_id", "message_id"),
        Index("ix_attachments_room_id", "room_id"),
    )


class ReadState(Base):
    __tablename__ = "read_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id", ondelete="CASCADE"))
    email: Mapped[str] = mapped_column(String(200))
    last_read_message_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    unread_count: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    room: Mapped["ChatRoom"] = relationship(back_populates="read_states")

    __table_args__ = (
        UniqueConstraint("room_id", "email", name="uq_read_states_room_email"),
        Index("ix_read_states_room_email", "room_id", "email"),
    )