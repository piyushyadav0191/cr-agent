from celery import Celery
from langchain_ollama import OllamaLLM
import requests
import json
import os

celery = Celery(
    "tasks",
    broker=f"redis://{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}/{os.getenv('REDIS_DB')}",
    backend=f"redis://{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}/{os.getenv('REDIS_DB')}",
    include=["celery_app"]
)

celery.conf.update(
    result_expires=3600,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
)

def fetch_pr_files(repo_url, pr_number, github_token=None):
    repo_path = repo_url.rstrip('/').replace("https://github.com/", "")
    github_api_url = f"https://api.github.com/repos/{repo_path}/pulls/{pr_number}/files"
    headers = {"Authorization": f"token {github_token}"} if github_token else {}
    response = requests.get(github_api_url, headers=headers)
    
    if response.status_code != 200:
        return {"error": "Failed to fetch PR files", "details": response.json()}

    files_data = response.json()
    files_content = []
    for file in files_data:
        raw_url = file.get("raw_url")
        if raw_url:
            file_response = requests.get(raw_url, headers=headers)
            if file_response.status_code == 200:
                files_content.append({"filename": file["filename"], "content": file_response.text})
            else:
                files_content.append({"filename": file["filename"], "error": "Failed to fetch content"})
    
    return files_content

def analyze_code_with_ai(code: str) -> list:
    ollama = OllamaLLM(
        base_url=os.getenv("OLLAMA_BASE_URL"),
        model=os.getenv("OLLAMA_MODEL")
    )
    prompt = f"""
    Analyze the following code and identify any issues, including:
    - Code style issues
    - Potential bugs
    - Performance improvements
    - Best practices

    Provide a JSON array with each issue formatted as:
    {{
        "type": "<type>",              # type can be "style", "bug", "performance", "best_practice"
        "line": <line_number or null>,  # Integer for the line number, or null if unknown
        "description": "<description>", # Brief description of the issue
        "suggestion": "<suggestion>"    # Suggested fix or improvement
    }}
    make sure to only return a valid JSON array and nothing before or after it. 
    I need to be able to parse your response directly as JSON.
    do not wrap the response in ```json ... ``` or similar. 
    directly return an array of issues like this: [
        {{"type": "bug", "line": 42, "description": "Potential division by zero", "suggestion": "Add a check for zero"}}
    ]


    Code:
    {code}
    """
    print('prompt', prompt)

    response = ollama.invoke(prompt)
    print('response', response)
    
    try:
        issues = json.loads(response) 
    except json.JSONDecodeError as e:
        return [{"error": "Failed to parse JSON from Ollama response", "details": str(e)}]

    structured_issues = [
        {
            "type": issue.get("type", "unknown"),
            "line": issue.get("line", None),
            "description": issue.get("description", "No description available"),
            "suggestion": issue.get("suggestion", "No suggestion available")
        }
        for issue in issues
    ]
    return structured_issues


@celery.task(bind=True)
def analyze_pr_task(self, pr_details):
    
    repo_url = pr_details['repo_url']
    pr_number = pr_details['pr_number']
    github_token = pr_details.get('github_token')

    files_content = fetch_pr_files(repo_url, pr_number, github_token)
    print('files_content', files_content)
    if "error" in files_content:
        return {"status": "error", "details": files_content["details"]}

    analysis_results = {
        "files": [],
        "summary": {
            "total_files": 0,
            "total_issues": 0,
            "critical_issues": 0
        }
    }

    for file in files_content:
        if "content" in file:
            issues = analyze_code_with_ai(file["content"])
            print('issues', issues)
            analysis_results["files"].append({
                "name": file["filename"],
                "issues": issues
            })
            analysis_results["summary"]["total_files"] += 1
            analysis_results["summary"]["total_issues"] += len(issues)
            analysis_results["summary"]["critical_issues"] += sum(1 for issue in issues if issue["type"] == "bug")
        else:
            analysis_results["files"].append({
                "name": file["filename"],
                "error": "Content not available"
            })

    return {
        "status": "completed",
        "results": analysis_results
    }
