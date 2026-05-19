# AgriAgent API Backend - FastAPI Main Entry

import asyncio
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.api.v1 import episodes, weekly, knowledge, stats, override, upload, chat, settings, vision, predict, memory, agent
from app.api.v1 import observability
from app.infra.chroma_store import chroma_manager
from app.infra.postgres import postgres_manager
from app.infra.redis_cache import redis_cache
from app.graph.builder_v2 import set_irrigation_graph_runtime
from app.graph.runtime import close_graph_runtime, create_async_graph_runtime, set_graph_runtime
from app.observability.instrumentation import observe_stack_status, setup_observability
from app.services.mcp_client import mcp_client


# 静态文件目录
PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "output"
DATA_DIR = PROJECT_ROOT / "data"
USER_LITERATURE_ASSETS_DIR = DATA_DIR / "user_literature" / "assets"
CHAT_ATTACHMENTS_DIR = DATA_DIR / "chat_attachments"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    print("AgriAgent API starting up...")
    await postgres_manager.connect()
    await redis_cache.connect()
    await chroma_manager.connect()
    runtime = await create_async_graph_runtime()
    set_graph_runtime(runtime)
    set_irrigation_graph_runtime(runtime)
    app.state.graph_runtime = runtime
    await mcp_client.connect()
    observe_stack_status(
        {
            "postgres": postgres_manager.status(),
            "redis": redis_cache.status(),
            "chroma": chroma_manager.status(),
            "mcp_connected": mcp_client.is_connected,
        }
    )
    try:
        yield
    finally:
        observe_stack_status(
            {
                "postgres": {"connected": False, "backend": postgres_manager.runtime.backend},
                "redis": {"connected": False, "backend": redis_cache.backend},
                "chroma": {"connected": False, "backend": chroma_manager.backend},
                "mcp_connected": False,
            }
        )
        await mcp_client.disconnect()
        runtime = getattr(app.state, "graph_runtime", None)
        if runtime is not None:
            await close_graph_runtime(runtime)
        await chroma_manager.close()
        await redis_cache.close()
        await postgres_manager.close()
        print("AgriAgent API shutting down...")


app = FastAPI(
    title="AgriAgent API",
    description="温室黄瓜灌水智能决策系统 API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Configuration - 允许所有本地开发端口
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
        "http://127.0.0.1:3003",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录
if OUTPUT_DIR.exists():
    app.mount("/static/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")
if (DATA_DIR / "images").exists():
    app.mount("/static/images", StaticFiles(directory=str(DATA_DIR / "images")), name="images")
USER_LITERATURE_ASSETS_DIR.mkdir(parents=True, exist_ok=True)
app.mount(
    "/static/user_literature/assets",
    StaticFiles(directory=str(USER_LITERATURE_ASSETS_DIR)),
    name="user_literature_assets",
)
CHAT_ATTACHMENTS_DIR.mkdir(parents=True, exist_ok=True)
app.mount(
    "/static/chat_attachments",
    StaticFiles(directory=str(CHAT_ATTACHMENTS_DIR)),
    name="chat_attachments",
)

setup_observability(app)

# Include routers
app.include_router(episodes.router, prefix="/api/episodes", tags=["Episodes"])
app.include_router(weekly.router, prefix="/api/weekly", tags=["Weekly"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["Knowledge"])
app.include_router(stats.router, prefix="/api/stats", tags=["Stats"])
app.include_router(override.router, prefix="/api/override", tags=["Override"])
app.include_router(upload.router, prefix="/api/upload", tags=["Upload"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(settings.router, prefix="/api", tags=["Settings"])
app.include_router(vision.router, prefix="/api", tags=["Vision"])
app.include_router(predict.router, prefix="/api", tags=["Predict"])
app.include_router(memory.router, prefix="/api/memory", tags=["Memory"])
app.include_router(observability.router, prefix="/api", tags=["Observability"])
app.include_router(agent.router, prefix="/api", tags=["Agent"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "AgriAgent API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    stack = {
        "postgres": postgres_manager.status(),
        "redis": redis_cache.status(),
        "chroma": chroma_manager.status(),
        "mcp_connected": mcp_client.is_connected,
    }
    observe_stack_status(stack)
    return {
        "status": "healthy",
        "message": "All systems operational",
        "stack": stack,
    }
