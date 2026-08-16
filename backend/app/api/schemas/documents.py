from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

DocumentStatusValue = Literal["uploading", "parsing", "indexing", "ready", "failed"]


class DocumentRead(BaseModel):
    # 可以直接从 orm 对象上读取属性
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    file_hash: str
    mime_type: str
    size: int
    status: DocumentStatusValue
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    items: list[DocumentRead]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)


_CONTENT_EXCERPT_LIMIT = 100


class DocumentChunkRead(BaseModel):
    id: UUID
    chunk_index: int
    page_no: int | None = None
    section_path: str | None = None
    content_excerpt: str
    char_count: int
    chunk_hash: str

    # 类方法装饰器，可以直接通过 类.方法(参数) 调用，cls为类本身
    @classmethod
    def from_orm_chunk(cls, chunk) -> "DocumentChunkRead":
        content = chunk.content or ""
        excerpt = content[:_CONTENT_EXCERPT_LIMIT]
        if len(content) > _CONTENT_EXCERPT_LIMIT:
            excerpt += "..."
        return cls(
            id=chunk.id,
            chunk_index=chunk.chunk_index,
            page_no=chunk.page_no,
            section_path=chunk.section_path,
            content_excerpt=excerpt,
            char_count=len(content),
            chunk_hash=chunk.chunk_hash,
        )


class DocumentChunkStats(BaseModel):
    total: int
    avg_length: int
    min_length: int
    max_length: int


class DocumentChunkListResponse(BaseModel):
    items: list[DocumentChunkRead]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    stats: DocumentChunkStats | None = None


class DocumentChunkDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    chunk_index: int
    page_no: int | None = None
    section_path: str | None = None
    content: str
    char_count: int
    chunk_hash: str
    created_at: datetime

    @classmethod
    def from_orm_chunk(cls, chunk) -> "DocumentChunkDetail":
        return cls(
            id=chunk.id,
            document_id=chunk.document_id,
            chunk_index=chunk.chunk_index,
            page_no=chunk.page_no,
            section_path=chunk.section_path,
            content=chunk.content,
            char_count=len(chunk.content or ""),
            chunk_hash=chunk.chunk_hash,
            created_at=chunk.created_at,
        )
