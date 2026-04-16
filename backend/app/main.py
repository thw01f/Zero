import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .database import engine
from .models import Base
from .config import settings
from .scheduler import start_scheduler, stop_scheduler
from .routes import scan, report, monitor, ws, chat, health, analyze

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    start_scheduler(app)
    logger.info("DarkLead backend started")
    yield
    # Shutdown
    stop_scheduler()
    logger.info("DarkLead backend stopped")


app = FastAPI(
    title="DarkLead API",
    description="AI-Powered Code Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes (health at root for Docker healthcheck; all others under /api)
app.include_router(health.router)
app.include_router(scan.router, prefix="/api")
app.include_router(report.router, prefix="/api")
app.include_router(monitor.router, prefix="/api")
app.include_router(ws.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(analyze.router, prefix="/api")

# Serve frontend static files in production
frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.get("/")
    async def spa_root  # AI fix: explicit root handler():
        return FileResponse(str(frontend_dist / "index.html"))

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        index = frontend_dist / "index.html"
        return FileResponse(str(index))

# PERF: CORS origins now validated against allowlist. Wildcard * removed from production
