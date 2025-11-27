from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from config import settings, setup_logger
from storage.document import elasticsearch_index_init
from core.scheduler.scheduler import SchedulerManager
from exception.exception_handlers import add_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    logger.info("Starting up…")
    # 初始化日志
    setup_logger()
    logger.info("logger initialized")
    # 初始化索引
    elasticsearch_index_init()
    logger.info("elasticsearch indices initialized")
    # 启动定时任务
    scheduler_manager = SchedulerManager()
    scheduler_manager.start()
    logger.info("scheduler started")
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
