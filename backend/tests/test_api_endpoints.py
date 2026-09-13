import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app

def test_api_health():
    async def _run():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get("/api/health")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "healthy"
            assert data["app"] == "BookMind"
            print("\nHealth check response:", data)

    asyncio.run(_run())
