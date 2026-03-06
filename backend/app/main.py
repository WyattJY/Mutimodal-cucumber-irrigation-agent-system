# AgriAgent API Backend - FastAPI Main Entry

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path

from app.api.v1 import episodes, weekly, knowledge, stats, override, upload, chat, settings, vision, predict, memory


# 静态文件目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
DATA_DIR = PROJECT_ROOT / "data"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    print("AgriAgent API starting up...")
    yield
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
    return {
        "status": "healthy",
        "message": "All systems operational",
    }
