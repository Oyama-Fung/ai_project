# 从根目录读取环境变量.env并暴露settings单例
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )

    app_name: str = "rag-knowledge-base"
    log_level: str = "INFO"
    # 数据库配置
    database_url: str = "postgresql+asyncpg://rag:rag@localhost:5433/rag_kb"
    # 腾讯云COS配置
    cos_secret_id: str = ""
    cos_secret_key: str = ""
    cos_bucket: str = ""
    cos_region: str = "ap-beijing"
    # 跨域配置
    cors_origins: str = "http://localhost:5173"
    # Embedding 模型配置
    embedding_api_key: str = ""
    embedding_base_url: str = ""
    embedding_model: str = ""
    embedding_dim: int = 1024
    embedding_batch_size: int = 10
    # 文档上传与切分
    upload_max_size_mb: int = 50
    chunk_size: int = 600
    chunk_overlap: int = 60
    # chat 模型配置
    chat_api_key: str = ""
    chat_base_url: str = ""
    chat_model: str = "qwen3.8-flash"

    # =======检索与问答=======
    # 检索 top-k: 交给 LLM 的候选 chunk 数量
    retrieval_top_k: int = 5
    # 拒答阈值: 当检索到的 chunk 与问题的相似度低于该阈值时，拒绝回答
    retrieval_min_score: float = 0.6
    # 多轮窗口：load_context 节点取最近多少轮塞进 promt
    chat_history_window: int = 5

    # ===== Query 优化（第 5 章）=====
    # 关掉后 route_query 节点强制走 original，方便对比有/无路由的效果
    query_route_enabled: bool = True
    # Multi-Query 策略生成的子查询数量，过大会增加 embedding 成本
    multi_query_count: int = 3

    # ===== 混合检索 =====
    # 每路（向量 / 关键词）召回数量；设计文档建议候选 20-50
    # 取 20 兼顾召回率与 RRF 融合开销
    retrieval_recall_top_k: int = 20
    # RRF 平滑常数，业界默认 60；越小越偏向高排名条目
    rrf_k: int = 60

    # ===== Agentic RAG =====
    # 关掉后图退化为单轮检索，作为单轮 vs agent 循环的对比开关
    agent_loop_enabled: bool = True
    # 最大检索轮次（含首轮）。LLM 决策最多触发 max_rounds-1 次再检索，避免循环调用
    agent_max_rounds: int = 3

    # ===== Reranker（DashScope qwen3-rerank，第 8 章）=====
    # 关掉后 rerank 节点直接透传，作为有/无精排的对比开关
    rerank_enabled: bool = True
    # DashScope rerank 端点，不是标准 OpenAI API
    rerank_base_url: str = ""
    rerank_model: str = "qwen3.7-text-rerank"
    # 留空时复用 chat_api_key（同一份 DashScope key，避免重复配置）
    rerank_api_key: str = ""
    # rerank Top1 相关度阈值；低于此值视为"上下文不足"由 judge_context 触发拒答
    # qwen3-rerank 输出 relevance_score ∈ [0, 1]，0.3 是经验值
    rerank_min_score: float = 0.3
    # 请求超时（秒），rerank 是同步调用主链路，超时要短一点避免拖慢回答
    rerank_timeout: float = 8.0

    # ===== 答案校验（第 8 章）=====
    # 关掉后跳过 verify_answer 调用，方便对比有/无引用支撑校验的效果
    verify_answer_enabled: bool = True

    # ===== LangSmith 可观测性 =====
    # 关掉后 @traceable / LangChain 自动 trace 全部降级为 no-op，trace_id 返回 None
    # 未配置 LangSmith key 时默认关闭，不影响本地启动
    langsmith_tracing: bool = False
    langsmith_api_key: str = ""
    langsmith_project: str = "rag-knowledge-base"
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    # LangSmith UI 私有 URL 前缀，形如 https://smith.langchain.com/o/{org}/projects/p/{project}
    # 包含 workspace/org 信息所以是私有的，配置后才下发跳转链接给前端
    langsmith_run_url_prefix: str = ""

    @property
    def observability_enabled(self) -> bool:
        """LangSmith 实际生效条件：开关打开 + key 已配置。任一缺失都视为关闭。"""
        return bool(self.langsmith_tracing and self.langsmith_api_key)

    @property
    def effective_rerank_api_key(self) -> str:
        """rerank_api_key 留空时回落到 chat_api_key，二者本来就是同一份 DashScope key。"""
        return self.rerank_api_key or self.chat_api_key

    @property
    def cos_configured(self) -> bool:
        return bool(self.cos_secret_id and self.cos_secret_key and self.cos_bucket)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
