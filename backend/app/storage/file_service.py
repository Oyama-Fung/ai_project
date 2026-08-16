from qcloud_cos.cos_exception import CosClientError, CosServiceError

from app.core.logging import get_logger
from app.storage.cos_client import CosClient, get_cos_client

logger = get_logger(__name__)


class FileService:
    def __init__(self, cos: CosClient | None = None) -> None:
        self._cos = cos or get_cos_client()

    @property
    def bucket(self) -> str:
        return self._cos.bucket

    @property
    def region(self) -> str:
        return self._cos.region

    @staticmethod
    def build_object_key(file_hash: str, suffix: str) -> str:
        # 用file_hash作为key天然幂等, 同文件多次上传命中同一object
        # suffix保留原扩展名, 方便在 cos 控制台直接点开预览
        return f"documents/{file_hash}{suffix}"

    async def upload(self, *, content: bytes, file_hash: str, suffix: str, mime_type: str) -> str:
        key = self.build_object_key(file_hash, suffix)
        await self._cos.put_object(key=key, body=content, content_type=mime_type)
        return key

    async def download(self, object_key: str) -> bytes:
        return await self._cos.get_object(object_key)

    async def delete(self, object_key: str) -> None:
        try:
            await self._cos.delete_object(object_key)
        except (CosClientError, CosServiceError) as exc:
            # 为什么只警告提示不重抛, 看仓库代码的注释
            logger.warning("cos delete failed: key=%s, err=%s", object_key, exc)


def get_file_service() -> FileService:
    return FileService()
