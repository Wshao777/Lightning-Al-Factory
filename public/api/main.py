import os
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional

import httpx
from fastapi import FastAPI, Request, HTTPException, Depends, Header
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from starlette.responses import Response

# --- Configuration ---
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/dbname")
MAX_POOL_SIZE = int(os.getenv("MAX_POOL_SIZE", "20"))
POOL_RECYCLE = int(os.getenv("POOL_RECYCLE", "3600"))
POOL_PRE_PING = os.getenv("POOL_PRE_PING", "true").lower() == "true"
MAX_CONNECTIONS = int(os.getenv("MAX_CONNECTIONS", "100"))
MAX_KEEPALIVE_CONNECTIONS = int(os.getenv("MAX_KEEPALIVE_CONNECTIONS", "20"))
FEDERATED_API_KEY = os.getenv("FEDERATED_API_KEY") # Should be set in env

# --- Shared Resources ---
class SharedResources:
    http_client: Optional[httpx.AsyncClient] = None
    db_engine: Optional[AsyncEngine] = None

shared = SharedResources()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize shared resources
    shared.http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(10.0, connect=5.0),
        limits=httpx.Limits(
            max_connections=MAX_CONNECTIONS,
            max_keepalive_connections=MAX_KEEPALIVE_CONNECTIONS
        )
    )
    shared.db_engine = create_async_engine(
        DATABASE_URL,
        pool_size=MAX_POOL_SIZE,
        max_overflow=10,
        pool_recycle=POOL_RECYCLE,
        pool_pre_ping=POOL_PRE_PING,
    )
    print("Lifespan start: Shared resources initialized.")
    yield
    # Clean up shared resources
    if shared.http_client:
        await shared.http_client.aclose()
    if shared.db_engine:
        await shared.db_engine.dispose()
    print("Lifespan end: Shared resources cleaned up.")

app = FastAPI(title="Federated APL - Commercial-Al-Smart", lifespan=lifespan)

# --- AsyncAPIClient for Federated Connections ---
class AsyncAPIClient:
    """Foundation for connecting to federated services."""
    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def forward_request(self, method: str, url: str, **kwargs) -> httpx.Response:
        try:
            # Filter out FastAPI specific kwargs if any, though here we control them
            response = await self.client.request(method, url, **kwargs)
            return response
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"Federated service error: {exc}")

# --- Dependencies ---
async def get_api_client() -> AsyncAPIClient:
    if not shared.http_client:
        raise RuntimeError("HTTP client not initialized")
    return AsyncAPIClient(shared.http_client)

async def verify_federated_auth(x_api_key: Optional[str] = Header(None)):
    """Mock federated authentication."""
    if not x_api_key or x_api_key != FEDERATED_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid Federated API Key")
    return {"identity": "Lightning Engineer", "role": "admin"}

# --- Smart Routing Logic ---
SERVICE_REGISTRY = {
    "ai_inference": "https://httpbin.org/anything/inference", # Using httpbin for real-ish proxy demo
    "data_warehouse": "https://httpbin.org/anything/data",
}

# --- Routes ---

@app.get("/")
async def root():
    return {"message": "Federated API Gateway Layer (APL) is Active", "status": "online"}

@app.api_route("/proxy/{service_name}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def smart_proxy(
    service_name: str,
    path: str,
    request: Request,
    api_client: AsyncAPIClient = Depends(get_api_client),
    auth_info: dict = Depends(verify_federated_auth)
):
    """
    Unified entry point with smart routing and identity pass-through.
    """
    if service_name not in SERVICE_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found in federation")

    target_base_url = SERVICE_REGISTRY[service_name]
    target_url = f"{target_base_url}/{path}"

    # Prepare headers for forwarding
    headers = dict(request.headers)
    # Remove host header to let httpx set it correctly for the target
    headers.pop("host", None)
    headers["X-Federated-Identity"] = auth_info["identity"]

    # Get request body if any
    body = await request.body()

    # Forward the request using AsyncAPIClient
    resp = await api_client.forward_request(
        method=request.method,
        url=target_url,
        headers=headers,
        params=dict(request.query_params),
        content=body
    )

    # Return the response from the federated service
    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=dict(resp.headers)
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
