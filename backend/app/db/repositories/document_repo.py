from uuid import UUID

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Document, DocumentStatus
from app.db.repositories.chunk_repo import _permission_where


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(
        self,
        document_id: UUID,
        *,
        permission_tags: list[str] | None = None,
    ) -> Document | None:
        """按 id 查文档；非 None permission_tags 时叠加可见性过滤。"""
        if permission_tags is None:
            return await self.session.get(Document, document_id)
        perm_where = _permission_where(permission_tags)
        stmt = select(Document).where(Document.id == document_id)
        if perm_where is not None:
            stmt = stmt.where(perm_where)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_by_hash(self, file_hash: str) -> Document | None:
        """根据文件hash获取文档（不是主键用不了get）"""
        stmt = select(Document).where(Document.file_hash == file_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add(self, document: Document) -> Document:
        """新增文档"""
        self.session.add(document)
        await self.session.flush()
        return document

    async def update_status(
        self,
        document_id: UUID,
        status: DocumentStatus,
        *,
        error_message: str | None = None,
    ) -> None:
        """更新文档状态"""
        doc = await self.get_by_id(document_id)
        if doc is None:
            return
        doc.status = status
        if error_message is not None or status != DocumentStatus.FAILED:
            doc.error_message = error_message

    async def list_paginated(
        self,
        page: int,
        page_size: int,
        *,
        status: DocumentStatus | None = None,
        permission_tags: list[str] | None = None,
    ) -> tuple[list[Document], int]:
        """分页查询文档，返回文档列表和总数"""
        offset = (page - 1) * page_size
        items_stmt = select(Document).order_by(Document.created_at.desc()).offset(offset).limit(page_size)
        count_stmt = select(func.count()).select_from(Document)
        if status is not None:
            items_stmt = items_stmt.where(Document.status == status)
            count_stmt = count_stmt.where(Document.status == status)
        perm_where: ColumnElement[bool] | None = _permission_where(permission_tags)
        if perm_where is not None:
            items_stmt = items_stmt.where(perm_where)
            count_stmt = count_stmt.where(perm_where)
        items = (await self.session.execute(items_stmt)).scalars().all()
        total = (await self.session.execute(count_stmt)).scalar_one()
        return list(items), int(total)

    async def delete(self, document: Document) -> None:
        """删除文档"""
        await self.session.delete(document)
