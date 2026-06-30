import os
import httpx
from fastapi import FastAPI, Request, HTTPException, Depends, Response
from contextlib import asynccontextmanager
from typing import Dict, Any

# --- Shared Resources ---
class AsyncAPIClient:
    def __init__(self):
        self.client = httpx.AsyncClient()

    async def close(self):
        await self.client.aclose()

    async def proxy_request(self, method: str, url: str, headers: Dict[str, str] = None, json: Any = None):
        try:
            response = await self.client.request(method, url, headers=headers, json=json)
            # Robustly handle different response types
            content_type = response.headers.get("Content-Type", "")
            if "application/json" in content_type:
                return response.json(), response.status_code, content_type
            else:
                return response.text, response.status_code, content_type
        except Exception as e:
            return {"error": str(e)}, 500, "application/json"

api_client = AsyncAPIClient()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize shared resources
    yield
    # Clean up
    await api_client.close()

app = FastAPI(title="Federated API Gateway (APL)", lifespan=lifespan)

# --- Federated Logic ---

# In a real scenario, these would be external URLs
MOCK_SERVICES = {
    "service-a": "http://127.0.0.1:8000/mock/service-a",
    "service-b": "http://127.0.0.1:8000/mock/service-b",
}

def get_federated_identity(request: Request):
    # Demonstrate Federated Identity/Authentication
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        # In a real sovereign SaaS, we might have complex JWT/Key validation here
        return "anonymous"
    return f"user:{auth_header[:10]}"

@app.get("/apl/{service_name}")
async def federated_gateway(service_name: str, request: Request, identity: str = Depends(get_federated_identity)):
    """
    Unified Entry & Smart Routing
    """
    if service_name not in MOCK_SERVICES:
        raise HTTPException(status_code=404, detail="Service not found in Federation")

    target_url = MOCK_SERVICES[service_name]

    # Smart Routing / Policy Execution
    # Add identity info to downstream request
    headers = {"X-Federated-Identity": identity}

    data, status_code, content_type = await api_client.proxy_request("GET", target_url, headers=headers)

    if status_code != 200:
        if isinstance(data, dict) and "error" in data:
             raise HTTPException(status_code=status_code, detail=data["error"])
        raise HTTPException(status_code=status_code, detail=str(data))

    # Return as a wrapped response or direct proxy
    return {
        "gateway": "Lightning Federated APL",
        "routed_to": service_name,
        "identity_context": identity,
        "response": data
    }

# --- Mock Backend Services (for demonstration) ---

@app.get("/mock/service-a")
async def mock_service_a(request: Request):
    identity = request.headers.get("X-Federated-Identity", "unknown")
    return {"message": "Hello from AI Inference Service A", "received_identity": identity}

@app.get("/mock/service-b")
async def mock_service_b(request: Request):
    identity = request.headers.get("X-Federated-Identity", "unknown")
    return {"message": "Data provided by Sovereign Data Hub B", "received_identity": identity}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "AAEC v8.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
