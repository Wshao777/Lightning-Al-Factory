import json
import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import httpx
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for DB and Pool configuration
# Use environment variables for sensitive data
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://user:password@localhost/lightning_db"
)
POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "20"))
MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))
POOL_RECYCLE = int(os.getenv("DATABASE_POOL_RECYCLE", "3600"))

# SQLAlchemy setup
# Note: Ensure the URL uses the asyncpg driver
if "postgresql://" in DATABASE_URL and "+asyncpg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(
    DATABASE_URL,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_recycle=POOL_RECYCLE,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()

# HTTP Client Pool setup using lifespan pattern for persistence and optimization
class HttpClientManager:
    def __init__(self):
        self.client: httpx.AsyncClient | None = None

    async def get_client(self) -> httpx.AsyncClient:
        if self.client is None:
            raise RuntimeError("HttpClientManager not initialized")
        return self.client

http_manager = HttpClientManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize optimized async connection pool for HTTP
    logger.info("Initializing async connection pools...")
    http_manager.client = httpx.AsyncClient(
        limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        timeout=httpx.Timeout(10.0)
    )
    yield
    # Graceful shutdown of pools
    logger.info("Closing async connection pools...")
    if http_manager.client:
        await http_manager.client.aclose()
    await engine.dispose()

app = FastAPI(title="Lightning AI Factory API", lifespan=lifespan)

# Dependency to get DB session
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

# Lightning Negotiation Engine Logic (Integrated as a service)
class LightningNegotiationService:
    def __init__(self):
        # Default config path relative to repository root
        self.config_path = ".github/workflows/ai_7f_factory_config.json"
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found at {self.config_path}. Using defaults.")
            self.config = {
                "project_name": "Lightning AI Factory",
                "narrative_persona": "Lightning AI"
            }

    def get_terms(self):
        return self.config

    async def generate_pitch(self, client: httpx.AsyncClient):
        # Demonstrate use of the optimized HTTP connection pool
        # In a real scenario, we might call external AI services or status checks
        # response = await client.get("https://api.lightning.ai/heartbeat")
        return f"Negotiation Pitch for {self.config['project_name']} generated successfully."

@app.get("/")
async def root():
    return {"message": "Lightning AI Factory API is active", "version": "v8.0"}

@app.get("/negotiate/pitch")
async def get_pitch(
    service: LightningNegotiationService = Depends(),
    client: httpx.AsyncClient = Depends(http_manager.get_client)
):
    pitch = await service.generate_pitch(client)
    return {"pitch": pitch, "terms": service.get_terms()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
