from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.error_handler import register_error_handlers
from app.api.routes import documents, health
from app.core.config import settings
from app.core.logging import configure_logging, get_logger


def create_app() -> FastAPI:
    configure_logging()
    logger = get_logger(__name__)
    logger.info("Starting application...")

    app = FastAPI(title=settings.app_name)

    # 注册中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(health.router, prefix="/api")
    app.include_router(documents.router, prefix="/api")

    # 注册错误处理器
    register_error_handlers(app)

    logger.info("Application started successfully: %s", settings.app_name)

    return app


app = create_app()
