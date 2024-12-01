import pytest
from httpx import AsyncClient

BASE_URL = "http://localhost:8000"

@pytest.mark.asyncio
async def test_analyze_pr():
    async with AsyncClient(base_url=BASE_URL) as client:
        response = await client.post(
            "/analyze-pr",
            json={
                "repo_url": "https://github.com/SciSaif/pack4print",
                "pr_number": 2
            }
        )
    assert response.status_code == 200
    assert "task_id" in response.json()

@pytest.mark.asyncio
async def test_status_endpoint():
    task_id = "sample_task_id"
    async with AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(f"/status/{task_id}")
    assert response.status_code == 200
    assert "status" in response.json()

@pytest.mark.asyncio
async def test_results_endpoint():
    task_id = "sample_task_id"
    async with AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(f"/results/{task_id}")
    assert response.status_code == 200
    assert "results" in response.json()
