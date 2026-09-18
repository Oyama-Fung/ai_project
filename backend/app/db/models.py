from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, Computed, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.db.base import Base


class DocumentStatus(StrEnum):
    """文档的声明周期状态
    uploading: 已写入COS,入库前
    parsing: Docling 解析中
    indexing: 切分+向量化+写chunk中
    ready: 可被检索
    failed: 任意阶段失败"""

    UPLOADING = "uploading"
    PARSING = "parsing"
    INDEXING = "indexing"
    READY = "ready"
    FAILED = "failed"


class Document(Base):
    """文档表，存储文档的元信息，文件存储在COS中，切分后的chunk存储在document_chunks表中"""

    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(512), nullable=False)

    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False)
    size: Mapped[int] = mapped_column(BigInteger, nullable=False)

    storage_provider: Mapped[str] = mapped_column(String(32), nullable=False, default="cos")
    cos_bucket: Mapped[str] = mapped_column(String(128), nullable=False)
    cos_object_key: Mapped[str] = mapped_column(String(512), nullable=False)
    cos_region: Mapped[str] = mapped_column(String(63), nullable=False)

    status: Mapped[DocumentStatus] = mapped_column(String(32), nullable=False, default=DocumentStatus.UPLOADING)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan", passive_deletes=True
    )


class DocumentChunk(Base):
    """chunk表，存储文档切分后的内容和向量化结果，向量化结果用于检索"""

    __tablename__ = "document_chunks"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(settings.embedding_dim), nullable=False)

    page_no: Mapped[int | None] = mapped_column(Integer, nullable=True)
    section_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_hash: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    extra_metadata: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    document: Mapped[Document] = relationship(back_populates="chunks")

    # 中文全文检索索引列。
    # GENERATED ALWAYS 由 PostgreSQL 根据 content 自动维护，应用层不写、只读。
    # SQLAlchemy 看到 Computed(persisted=True) 会自动从 INSERT/UPDATE 中排除该列。
    content_tsv: Mapped[str] = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('chinese_zh', content)", persisted=True),
        nullable=False,
    )


class MessageRole(StrEnum):
    """消息角色"""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class Conversation(Base):
    """会话表，存储用户的会话信息"""

    __tablename__ = "conversations"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(256), nullable=False, default="新对话")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Message.created_at",
    )


class Message(Base):
    """消息表，存储会话中的消息"""

    __tablename__ = "messages"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[MessageRole] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    extra_metadata: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    conversation: Mapped[Conversation] = relationship(back_populates="messages")
    citations: Mapped[list["AnswerCitation"]] = relationship(
        back_populates="message",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="AnswerCitation.ordinal",
    )


class AnswerCitation(Base):
    """
    消息引用表，存储消息中引用的文档chunk信息。
    冗余 page_no / quote 的作用：原 chunk 被删除或者覆盖
    """

    __tablename__ = "answer_citations"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    message_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # promt 中给 llm 看到的 片段N 编号，从1开始
    # 持久化下来才能保证刷新后引用顺序与 llm 当时看到的一致（id是随机的不能用来排序）
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    # 原文档/chunk可能被删除，所以 ON DELETE SET NULL, 保留快照
    document_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
    )
    chunk_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("document_chunks.id", ondelete="SET NULL"),
        nullable=True,
    )
    document_name: Mapped[str] = mapped_column(String(512), nullable=False)
    page_no: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quote: Mapped[str] = mapped_column(Text, nullable=False)

    message: Mapped[Message] = relationship(back_populates="citations")

    # 混合检索调试元数据：sources / vector_rank / keyword_rank / *_score / rrf_score
    # 用 JSONB 而非拆列，后续 reranker 章节会继续往里加字段，schema 不稳定时更友好
    retrieval_meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
