from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Document, DocumentChunk


@dataclass(frozen=True)
class ChunkStats:
    """单个文档下的 chunk 长度与数量统计，全部 None 表示文档没有任何 chunk。"""

    total: int
    avg_length: int
    min_length: int
    max_length: int


class DocumentChunkRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def bulk_add(self, chunks: Sequence[DocumentChunk]) -> None:
        """批量新增 chunk"""
        if not chunks:
            return
        self.session.add_all(chunks)
        await self.session.flush()

    async def delete_by_document(self, document_id: UUID) -> None:
        """删除指定文档的所有 chunk"""
        stmt = delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
        await self.session.execute(stmt)

    async def list_paginated_by_document(
        self,
        document_id: UUID,
        page: int,
        page_size: int,
    ) -> tuple[list[DocumentChunk], int]:
        """分页查询指定文档的 chunk，返回 chunk 列表和总数"""
        offset = (page - 1) * page_size
        items_stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index.asc())
            .offset(offset)
            .limit(page_size)
        )
        count_stmt = select(func.count()).select_from(DocumentChunk).where(DocumentChunk.document_id == document_id)
        items = (await self.session.execute(items_stmt)).scalars().all()
        total = (await self.session.execute(count_stmt)).scalar_one()
        return list(items), int(total)

    async def get_for_document(self, document_id: UUID, chunk_id: UUID) -> DocumentChunk | None:
        """获取指定文档下的 chunk"""
        stmt = select(DocumentChunk).where(DocumentChunk.id == chunk_id, DocumentChunk.document_id == document_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_stats(self, document_id: UUID) -> ChunkStats | None:
        """获取指定文档下的 chunk 统计信息"""
        length = func.char_length(DocumentChunk.content)
        stmt = select(
            func.count().label("total"),
            func.avg(length).label("avg_len"),
            func.min(length).label("min_len"),
            func.max(length).label("max_len"),
        ).where(DocumentChunk.document_id == document_id)
        row = (await self.session.execute(stmt)).one()
        if not row.total:
            return None
        return ChunkStats(
            total=int(row.total),
            avg_length=int(row.avg_len or 0),
            min_length=int(row.min_len or 0),
            max_length=int(row.max_len or 0),
        )

    async def vector_search(
        self,
        query_embedding: list[float],
        top_k: int,
    ) -> list[tuple[DocumentChunk, float]]:
        """按 cosine 距离做 Top-K 向量检索。

        - 仅检索状态为 ready 的文档（避免拿到尚未完成入库的脏 chunk）
        - 返回 (chunk, distance) 列表，distance 越小越相似（pgvector cosine_distance）
        - 用 selectinload 把所属 Document 一并加载，方便上层直接读 document.name
          而不会再发 N 次 lazy load 查询
        """
        distance = DocumentChunk.embedding.cosine_distance(query_embedding)

        stmt = (
            select(DocumentChunk, distance.label("distance"))
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(Document.status == "ready")
            .order_by(distance.asc())
            .limit(top_k)
            .options(selectinload(DocumentChunk.document))
        )
        rows = (await self.session.execute(stmt)).all()
        return [(chunk, float(dist)) for chunk, dist in rows]
