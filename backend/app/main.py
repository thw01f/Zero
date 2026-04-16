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