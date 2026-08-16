# 腾讯云 COS 客户端封装

import asyncio

from qcloud_cos import CosConfig, CosS3Client
from qcloud_cos.cos_exception import CosClientError, CosServiceError

from app.core.config import settings
from app.core.exception import ConfigurationError
from app.core.logging import get_logger

logger = get_logger(__name__)


class CosClient:
    def __init__(self) -> None:
        if not settings.cos_configured:
            raise ConfigurationError(
                "腾讯云 COS 配置不完整, 请检查环境变量 .env 中的 cos_secret_id、"
                "cos_secret_key 和 cos_bucket 是否已正确设置。"
            )

        config = CosConfig(
            Region=settings.cos_region, SecretId=settings.cos_secret_id, SecretKey=settings.cos_secret_key
        )
        self._client = CosS3Client(config)
        self._bucket = settings.cos_bucket

    @property
    def bucket(self) -> str:
        return self._bucket

    @property
    def region(self) -> str:
        return settings.cos_region

    async def ping(self) -> bool:
        try:
            await asyncio.to_thread(self._client.head_bucket, Bucket=self._bucket)
            return True
        except (CosServiceError, CosClientError) as e:
            logger.error(f"腾讯云 COS 连接失败: {e}")
            return False

    async def put_object(self, *, key: str, body: bytes, content_type: str) -> None:
        # 上传字节流到指定 object key。同名覆盖。
        await asyncio.to_thread(
            self._client.put_object,
            Bucket=self._bucket,
            Key=key,
            Body=body,
            ContentType=content_type,
        )

    async def get_object(self, key: str) -> bytes:
        # 读取 object 全部字节
        def _read() -> bytes:
            response = self._client.get_object(Bucket=self._bucket, Key=key)
            # sdk 返回的 Body 是流式对象, get_raw_stream 拿到原始 stream
            return response["Body"].get_raw_stream().read()

        return await asyncio.to_thread(_read)

    async def delete_object(self, key: str) -> None:
        # 删除指定 object
        await asyncio.to_thread(self._client.delete_object, Bucket=self._bucket, Key=key)


_cos_client: CosClient | None = None


def get_cos_client() -> CosClient:
    global _cos_client
    if _cos_client is None:
        _cos_client = CosClient()
    return _cos_client
