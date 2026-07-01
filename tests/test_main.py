import pytest
from httpx import AsyncClient, ASGITransport
import sys
import os
import asyncio
import httpx

# Add public/api to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'public', 'api')))

from main import app, shared

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture(autouse=True)
async def manage_lifespan():
    from main import lifespan
    async with lifespan(app):
        yield

@pytest.mark.anyio
async def test_root():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Federated API Gateway Layer (APL) is Active", "status": "online"}

@pytest.mark.anyio
async def test_proxy_unauthorized():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/proxy/ai_inference/predict")
    assert response.status_code == 401
    assert "Unauthorized" in response.json()["detail"]

@pytest.mark.anyio
async def test_proxy_authorized_success(monkeypatch):
    # Use a simpler mocking approach by mocking the forward_request method of AsyncAPIClient
    from main import AsyncAPIClient as RealAsyncAPIClient

    async def mock_forward_request(self, method, url, **kwargs):
        identity = kwargs.get("headers", {}).get("X-Federated-Identity")
        return httpx.Response(200, json={"mocked": "true", "identity": identity})

    monkeypatch.setattr(RealAsyncAPIClient, "forward_request", mock_forward_request)

    headers = {"X-API-Key": "lightning-secret-key"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/proxy/ai_inference/predict", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["mocked"] == "true"
    assert data["identity"] == "Lightning Engineer"

@pytest.mark.anyio
async def test_proxy_service_not_found():
    headers = {"X-API-Key": "lightning-secret-key"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/proxy/unknown_service/path", headers=headers)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]
