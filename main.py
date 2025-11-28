from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from config import settings, setup_logger
from storage.document import init_elasticsearch
from storage.database import init_database
from core.scheduler.scheduler import SchedulerManager
from exception.exception_handlers import add_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 初始化日志
    setup_logger()
    # 启动时执行
    logger.info("application starting up")
    # 初始化数据库
    init_database()
    logger.info("database initialized")
    # 初始化索引
    init_elasticsearch()
    logger.info("elasticsearch initialized")
    # 启动定时任务
    scheduler_manager = SchedulerManager()
    scheduler_manager.start()
    logger.info("scheduler started")
    logger.info(f"application initialized with {settings.server.host}:{settings.server.port}")
    logger.info("application startup complete")
    yield

    # 关闭时执行
    scheduler_manager.stop()
    logger.info("scheduler shutting down..")
    logger.info("App shutting down...")


app = FastAPI(
    lifespan=lifespan
)
# 跨域
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"chrome-extension://[a-z]{32}",
    allow_origins=["*"],  # 允许的域名，开发可用 "*"，生产建议指定
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# 异常处理
add_exception_handlers(app)
# ---路由---
# 挂载 API
# app.include_router(subject_common_router, prefix="/tech")
# 挂载前端 ui 目录
app.mount('/', StaticFiles(directory=settings.server.static_path, html=True), name="ui")

if __name__ == "__main__":
    """
        服务启动
        workers 强制为1
    """
    uvicorn.run("main:app", host=settings.server.host, port=settings.server.port, reload=True, workers=1)
