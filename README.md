# CR Agent

An AI-powered autonomous code review agent designed to analyze GitHub pull requests (PRs). It offers detailed feedback on code style, potential bugs, performance enhancements, and best practices. This system handles pull requests asynchronously and communicates with developers through a structured API.

## Project Setup Instructions

### Prerequisites

-   Docker and Docker Compose

### Step 1: Navigate to the Project Directory

```bash
cd cr-agent
```

### Step 2: Configure Environment Variables

Create a .env file in the project root directory, and specify the following:

```bash
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=deepseek-coder-v2
```

### Step 3: Build and Start the Docker Containers

```bash
docker-compose up --build
```

### Step 4: Install the deepseek-coder-v2 model in Ollama

make sure you are in the project root directory and run the following command:

```bash
docker-compose exec ollama ollama run deepseek-coder-v2
```

Make sure the model is installed successfully before conitnuing to the next step.

### Step 5: Test the Setup

After the containers are up and running, test the API using the endpoints described in the API documentation below.

## API Documentation

### 1. POST /analyze-pr

Initiates the code analysis for a specified GitHub pull request (PR).

Request:

-   URL: /analyze-pr
-   Method: POST
-   Body:
    ```json
    {
        "repo_url": "https://github.com/user/repo",
        "pr_number": 123,
        "github_token": "optional_token"
    }
    ```

Response:

-   200 OK

```json
{
    "task_id": "abc123",
    "status": "submitted"
}
```

### 2. GET /status/{task_id}

Checks the status of an analysis task.

Request:

-   URL: /status/{task_id}
-   Method: GET

Response:

-   200 OK

```json
{
    "task_id": "abc123",
    "status": "completed"
}
```

### 3. GET /results/{task_id}

Retrieves the analysis results for a specified task.

Request:

-   URL: /results/{task_id}
-   Method: GET

Response:

-   200 OK

```json
{
    "task_id": "abc123",
    "status": "completed",
    "results": {
        "files": [
            {
                "name": "main.py",
                "issues": [
                    {
                        "type": "style",
                        "line": 15,
                        "description": "Line too long",
                        "suggestion": "Break line into multiple lines"
                    },
                    {
                        "type": "bug",
                        "line": 23,
                        "description": "Potential null pointer",
                        "suggestion": "Add null check"
                    }
                ]
            }
        ],
        "summary": {
            "total_files": 1,
            "total_issues": 2,
            "critical_issues": 1
        }
    }
}
```

## Testing

```bash
pytest tests/test_api.py
```