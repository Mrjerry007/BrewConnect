from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

user_interests_table = Table(
    "user_interests", Base.metadata,
    Column("user_id",     Integer, ForeignKey("users.id",     ondelete="CASCADE"), primary_key=True),
    Column("interest_id", Integer, ForeignKey("interests.id", ondelete="CASCADE"), primary_key=True),
)

class User(Base):
    __tablename__ = "users"
    id              = Column(Integer, primary_key=True, index=True)
    username        = Column(String(50),  unique=True, nullable=False, index=True)
    email           = Column(String(120), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    display_name    = Column(String(100), nullable=False)
    bio             = Column(Text, default="")
    avatar_url      = Column(String(255), default="")
    created_at      = Column(DateTime, server_default=func.now())
    interests       = relationship("Interest", secondary=user_interests_table, back_populates="users", lazy="selectin")
    active_session  = relationship("ActiveSession", back_populates="user",
                                   uselist=False, cascade="all, delete-orphan")
    messages_sent   = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender", cascade="all, delete-orphan")
    messages_received = relationship("Message", foreign_keys="Message.recipient_id", back_populates="recipient", cascade="all, delete-orphan")

class Interest(Base):
    __tablename__ = "interests"
    id   = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    users = relationship("User", secondary=user_interests_table, back_populates="interests")

class ActiveSession(Base):
    __tablename__ = "active_sessions"
    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    latitude     = Column(Float,   nullable=False)
    longitude    = Column(Float,   nullable=False)
    is_active    = Column(Boolean, default=True, nullable=False)
    venue_name   = Column(String(100), default="")
    mood_tag     = Column(String(50),  default="")
    last_seen    = Column(DateTime, server_default=func.now(), onupdate=func.now())
    activated_at = Column(DateTime, server_default=func.now())
    user         = relationship("User", back_populates="active_session")

class Message(Base):
    __tablename__ = "messages"
    id           = Column(Integer, primary_key=True, index=True)
    sender_id    = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    recipient_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content      = Column(Text, nullable=False)
    created_at   = Column(DateTime, server_default=func.now(), index=True)
    is_read      = Column(Boolean, default=False, nullable=False)
    
    sender       = relationship("User", foreign_keys=[sender_id], back_populates="messages_sent")
    recipient    = relationship("User", foreign_keys=[recipient_id], back_populates="messages_received")