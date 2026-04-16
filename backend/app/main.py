import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .database import engine, SessionLocal
from .models import Base, User
from .config import settings
from .scheduler import start_scheduler, stop_scheduler
from .routes import scan, report, monitor, ws, chat, health, analyze
from .routes import auth as auth_router
from .routes import profile as profile_router
from .routes import models as models_router
from .routes import graph as graph_router
from .routes import settings as settings_router
from .routes import proxy as proxy_router
from .routes.auth import hash_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _seed_admin() -> None:
    """Create default admin account if it doesn't exist."""
    import uuid
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == "admin").first():
            db.add(User(
                id=str(uuid.uuid4()),
                email="admin@darklead.local",
                username="admin",
                full_name="Administrator",
                hashed_password=hash_password("zero"),
                avatar_color="#1a73e8",
                role="admin",
                is_active=True,
            ))
            db.commit()
            logger.info("Default admin account created (admin / zero)")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    _seed_admin()
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
app.include_router(auth_router.router, prefix="/api")
app.include_router(profile_router.router, prefix="/api")
app.include_router(models_router.router, prefix="/api")
app.include_router(graph_router.router, prefix="/api")
app.include_router(settings_router.router, prefix="/api")
app.include_router(proxy_router.router, prefix="/api")

# Serve frontend static files in production
frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.get("/")
    async def spa_root():
        return FileResponse(str(frontend_dist / "index.html"))

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        index = frontend_dist / "index.html"
        return FileResponse(str(index))

# PERF: CORS origins now validated against allowlist. Wildcard * removed from production
