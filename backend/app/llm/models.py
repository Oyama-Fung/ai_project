from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.core.exception import ConfigurationError

_chat_model: BaseChatModel | None = None


def get_chat_model() -> BaseChatModel:
    """返回流式 ChatOpenAI 实例（单例缓存：模型客户端持有 httpx 连接池，反复创建会浪费资源）"""
    global _chat_model
    if _chat_model is not None:
        return _chat_model

    if not settings.chat_api_key:
        raise ConfigurationError("未配置 chat_api_key，请在环境变量中设置")

    _chat_model = ChatOpenAI(
        model=settings.chat_model,
        api_key=settings.chat_api_key,
        base_url=settings.chat_base_url,
        # 知识库问答 + 严格的引用编号约束属于指令遵循任务，温度设0
        # 避免 n编号 在不同 chunk 间漂移
        temperature=0,
        streaming=True,
    )

    return _chat_model
