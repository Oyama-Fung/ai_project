import hashlib

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings


def _bulid_splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        length_function=len,
        separators=[
            "\n\n",
            "\n",
            " ",
            "",
            "。",
            "！",
            "？",
            "：",
            "，",
        ],
        is_separator_regex=False,
    )


def split(documents: list[Document]) -> list[Document]:
    """切分并补齐 chunk 级 metadata"""
    splitter = _bulid_splitter()
    chunks = splitter.split_documents(documents)

    for index, chunk in enumerate(chunks):
        # 补齐 metadata
        chunk.metadata["chunk_index"] = index
        chunk.metadata["chunk_hash"] = hashlib.md5(chunk.page_content.encode("utf-8")).hexdigest()

    return chunks
