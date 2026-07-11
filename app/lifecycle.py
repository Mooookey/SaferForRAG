from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.services.container import ServiceContainer


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ---------- 启动阶段（yield 之前） ----------
    print("🚀 应用启动：正在连接数据库...")
    app.state.service_container=ServiceContainer()
    
    # 关键点：yield 把控制权交还给 FastAPI，让应用开始接收请求
    yield
    
    # ---------- 关闭阶段（yield 之后） ----------
    print("🛑 应用关闭：正在释放资源...")

    print("✅ 资源已清理完毕。")