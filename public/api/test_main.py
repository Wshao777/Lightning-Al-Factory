import pytest
from httpx import ASGITransport, AsyncClient
from public.api.main import app

@pytest.mark.anyio
async def test_root():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Trigger lifespan
        async with app.router.lifespan_context(app):
            response = await ac.get("/")
            assert response.status_code == 200
            assert response.json() == {"message": "Federated API Gateway Layer is Active"}

@pytest.mark.anyio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        async with app.router.lifespan_context(app):
            response = await ac.get("/health")
            assert response.status_code == 200
            assert response.json() == {"status": "healthy"}

@pytest.mark.anyio
async def test_federated_404():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        async with app.router.lifespan_context(app):
            response = await ac.get("/federated/unknown-service/path")
            assert response.status_code == 404
            assert response.json() == {"detail": "Federated service not found"}
