from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from celery.result import AsyncResult
from celery_app import analyze_pr_task 

app = FastAPI()

class PRRequest(BaseModel):
    repo_url: str
    pr_number: int
    github_token: str = None
    


@app.post("/analyze-pr")
async def analyze_pr(pr_request: PRRequest):
    task = analyze_pr_task.delay(pr_request.dict())
    return {"task_id": task.id, "status": "submitted"}

@app.get("/status/{task_id}")
async def get_task_status(task_id: str):
    result = AsyncResult(task_id)
    return {"task_id": task_id, "status": result.status}

@app.get("/results/{task_id}")
async def get_task_results(task_id: str):
    result = AsyncResult(task_id)
    print('result', result)
    if result.status == "SUCCESS":
        return {"task_id": task_id, "status": result.status, "results": result.result}
    elif result.status == "PENDING":
        return {"task_id": task_id, "status": "pending", "results": None}
    elif result.status == "FAILURE":
        return {"task_id": task_id, "status": "failed", "results": str(result.result)}
    else:
        raise HTTPException(status_code=404, detail="Results not available yet")