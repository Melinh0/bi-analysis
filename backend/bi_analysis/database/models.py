from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Enum, Index, Float, Boolean, JSON
)
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
from enum import Enum as PyEnum


Base = declarative_base()


class SourceType(PyEnum):
    INSTAGRAM = "instagram"


    KNEWIN = "knewin"
    TWITTER = "twitter"  # mantido apenas para exibir jobs antigos; fonte removida
    YOUTUBE = "youtube"
    REDDIT = "reddit"
    WIKIPEDIA = "wikipedia"
    MANUAL = "manual"
    TIKTOK = "tiktok"


class ContentType(PyEnum):
    POST = "post"
    COMMENT = "comment"
    REEL = "reel"
    NEWS = "news"
    TWEET = "tweet"
    VIDEO = "video"
    CHANNEL = "channel"
    SEARCH = "search"
    SUBMISSION = "submission"
    TOPIC = "topic"
    REPORT = "report"
    PROFILE = "profile"
    HASHTAG = "hashtag"


class ExtractionJob(Base):
    __tablename__ = "extraction_jobs"

    id = Column(Integer, primary_key=True, index=True)
    source_type = Column(Enum(SourceType), nullable=False)
    content_type = Column(Enum(ContentType), nullable=False)
    query_params = Column(JSON, nullable=True)
    status = Column(String(50), default="pending")
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    items_extracted = Column(Integer, default=0)
    items_stored = Column(Integer, default=0)

    extracted_items = relationship("ExtractedItem", back_populates="job")


class ExtractedItem(Base):
    __tablename__ = "extracted_items"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("extraction_jobs.id"), nullable=False)
    source_type = Column(Enum(SourceType), nullable=False)
    content_type = Column(Enum(ContentType), nullable=False)
    external_id = Column(String(255), nullable=True, index=True)
    url = Column(String(1000), nullable=True)
    author = Column(String(255), nullable=True)
    author_id = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)

    extra_data = Column("metadata", JSON, nullable=True)
    published_at = Column(DateTime, nullable=True, index=True)
    extracted_at = Column(DateTime, default=datetime.utcnow, index=True)
    processed = Column(Boolean, default=False)
    vector_id = Column(String(255), nullable=True, index=True)

    job = relationship("ExtractionJob", back_populates="extracted_items")
    embeddings = relationship("Embedding", back_populates="item")


class Embedding(Base):
    __tablename__ = "embeddings"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("extracted_items.id"), nullable=False)
    vector_id = Column(String(255), unique=True, nullable=False, index=True)
    model = Column(String(100), nullable=False)
    dimension = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    item = relationship("ExtractedItem", back_populates="embeddings")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    report_type = Column(String(100), nullable=False)
    template = Column(String(100), nullable=True)
    parameters = Column(JSON, nullable=True)
    generated_content = Column(Text, nullable=True)
    status = Column(String(50), default="draft")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    generated_at = Column(DateTime, nullable=True)
    created_by = Column(String(255), nullable=True)


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=True)
    context_filter = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship(
        "ChatMessage", back_populates="session", cascade="all, delete-orphan"
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)

    extra_data = Column("metadata", JSON, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    model = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ChatSession", back_populates="messages")


class ScheduledJob(Base):
    __tablename__ = "scheduled_jobs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    source_type = Column(Enum(SourceType), nullable=False)
    content_type = Column(Enum(ContentType), nullable=False)
    query_params = Column(JSON, nullable=True)
    cron_expression = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    last_run = Column(DateTime, nullable=True)
    next_run = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


Index("ix_extracted_items_source_type_content_type", ExtractedItem.source_type, ExtractedItem.content_type)
Index("ix_extracted_items_processed", ExtractedItem.processed)
