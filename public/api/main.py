import os
import httpx
from fastapi import FastAPI, Request, HTTPException, Response
from contextlib import asynccontextmanager
from typing import Optional
from dotenv import load_dotenv
from pathlib import Path

# Use absolute path for .env file
BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_path = BASE_DIR / "private_core" / "secrets.env"
load_dotenv(dotenv_path=env_path)

class AsyncAPIClient:
    """
    Federated API Client for proxying requests to external services.
    Handles authentication and identity propagation.
    """
    def __init__(self, limits: Optional[httpx.Limits] = None):
        # Good practice: pool_recycle and pool_pre_ping equivalents or timeouts
        self.client = httpx.AsyncClient(
            limits=limits or httpx.Limits(max_keepalive_connections=5, max_connections=10),
            timeout=httpx.Timeout(10.0, connect=5.0)
        )

    async def close(self):
        await self.client.aclose()

    async def proxy_request(self, method: str, url: str, request: Request) -> httpx.Response:
        """
        Proxies an incoming request to an external service.
        """
        headers = dict(request.headers)
        # Remove host header to avoid issues with some servers
        headers.pop("host", None)

        # Propagate identity if available
        federated_identity = request.headers.get("X-Federated-Identity")
        if federated_identity:
            headers["X-Federated-Identity"] = federated_identity

        # Add internal API key for the federated service
        api_key = os.getenv("FEDERATED_API_KEY")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            body = await request.body()
            response = await self.client.request(
                method,
                url,
                headers=headers,
                params=request.query_params,
                content=body
            )
            return response
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"Error contacting federated service: {exc}")

# Global API Client
api_client: Optional[AsyncAPIClient] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize resources
    global api_client
    api_client = AsyncAPIClient()
    yield
    # Clean up resources
    if api_client:
        await api_client.close()

app = FastAPI(title="Commercial-Al-Smart Federated APL", lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "Federated API Gateway Layer is Active"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.api_route("/federated/{service_name}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def federated_proxy(service_name: str, path: str, request: Request):
    """
    Smart Routing: Dynamically routes requests based on service_name.
    """
    # Dynamic routing logic - Consider moving to config/registry later
    service_urls = {
        "service-a": os.getenv("EXTERNAL_SERVICE_A_URL", "http://localhost:8001"),
        "service-b": os.getenv("EXTERNAL_SERVICE_B_URL", "http://localhost:8002"),
    }

    base_url = service_urls.get(service_name)
    if not base_url:
        raise HTTPException(status_code=404, detail="Federated service not found")

    target_url = f"{base_url}/{path}"

    if api_client is None:
         raise HTTPException(status_code=500, detail="API client not initialized")

    proxied_response = await api_client.proxy_request(request.method, target_url, request)

    # Correctly propagate status code, headers and content
    # Exclude certain headers like 'content-encoding', 'transfer-encoding', 'connection'
    excluded_headers = ["content-encoding", "transfer-encoding", "connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailers", "upgrade"]
    headers = {k: v for k, v in proxied_response.headers.items() if k.lower() not in excluded_headers}

    return Response(
        content=proxied_response.content,
        status_code=proxied_response.status_code,
        headers=headers
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
