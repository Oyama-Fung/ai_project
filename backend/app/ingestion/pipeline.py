from uuid import UUID

from app.core.logging import get_logger
from app.db.models import DocumentChunk, DocumentStatus
from app.db.repositories.chunk_repo import DocumentChunkRepository
from app.db.repositories.document_repo import DocumentRepository
from app.db.session import AsyncSessionLocal
from app.ingestion import embedder, parser, splitter
from app.storage.file_service import get_file_service

logger = get_logger(__name__)


async def _set_status(
    document_id: UUID,
    status: DocumentStatus,
    *,
    error_message: str | None = None,
) -> None:
    """状态变更独立事务：避免长事务，保证前端轮询能立即看到中间态。"""
    async with AsyncSessionLocal() as session:
        repo = DocumentRepository(session)
        await repo.update_status(document_id, status, error_message=error_message)
        await session.commit()


async def ingest_document(document_id: UUID) -> None:
    """执行完整入库流程：解析、分块、向量化、入库。任何步骤失败都会抛出异常，sqlalchemy自动事务回滚。"""
    logger.info("开始入库 document_id=%s", document_id)
    try:
        async with AsyncSessionLocal() as session:
            doc_repo = DocumentRepository(session)
            document = await doc_repo.get_by_id(document_id)
            if document is None:
                logger.warning("文档不存在 document_id=%s", document_id)
                return
            object_key = document.cos_object_key
            filename = document.name

        await _set_status(document_id, DocumentStatus.PARSING)
        content = await get_file_service().download(object_key)
        documents = await parser.parse(filename, content)

        await _set_status(document_id, DocumentStatus.INDEXING)
        chunks = splitter.split(documents)
        logger.info("切分好的chunks：%s", chunks)
        if not chunks:
            raise ValueError("切分后没有任何chunks，请检查文档内容")

        embeddings = await embedder.get_embeddings().aembed_documents([c.page_content for c in chunks])

        async with AsyncSessionLocal() as session:
            chunk_repo = DocumentChunkRepository(session)
            chunk_repo.session.add_all(
                [
                    DocumentChunk(
                        document_id=document_id,
                        content=c.page_content,
                        embedding=vec,
                        page_no=c.metadata.get("page_no"),
                        section_path=c.metadata.get("section_path"),
                        chunk_index=c.metadata["chunk_index"],
                        chunk_hash=c.metadata["chunk_hash"],
                        extra_metadata=c.metadata,
                    )
                    for c, vec in zip(chunks, embeddings, strict=True)
                ]
            )
            await session.commit()

        await _set_status(document_id, DocumentStatus.READY, error_message=None)
        logger.info("入库完成 document_id=%s, chunks=%d", document_id, len(chunks))

    except Exception as exc:
        logger.error("入库失败 document_id=%s, error=%s", document_id, str(exc))
        message = str(exc).strip() or exc.__class__.__name__
        # 截断，避免过长
        await _set_status(document_id, DocumentStatus.FAILED, error_message=message[:500])
