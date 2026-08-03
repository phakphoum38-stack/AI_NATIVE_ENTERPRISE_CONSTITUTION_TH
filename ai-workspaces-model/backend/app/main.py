from __future__ import annotations
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .models import (
    AiRequest, AiResponse, Branch, BranchCreate, Commit, CommitCreate,
    PullRequest, PullRequestCreate, PullStatus, Repository, RepositoryCreate,
)
from .services import AiService, WorkflowService
from .store import store

app = FastAPI(title="AI Workspaces Model API", version="0.1.0")
FRONTEND = Path(__file__).resolve().parents[2] / "frontend"
app.mount("/assets", StaticFiles(directory=FRONTEND), name="assets")

@app.get("/")
def index() -> FileResponse:
    return FileResponse(FRONTEND / "index.html")

@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ai-workspaces-model"}

@app.get("/api/repositories", response_model=list[Repository])
def list_repositories() -> list[Repository]:
    return list(store.repositories.values())

@app.post("/api/repositories", response_model=Repository, status_code=201)
def create_repository(payload: RepositoryCreate) -> Repository:
    repo = Repository(id=store.new_id(), **payload.model_dump())
    with store.lock:
        store.repositories[repo.id] = repo
        main = Branch(id=store.new_id(), repository_id=repo.id, name="main")
        store.branches[repo.id]["main"] = main
        store.log("repository.create", repo.name)
    return repo

def require_repo(repository_id: str) -> Repository:
    repo = store.repositories.get(repository_id)
    if not repo:
        raise HTTPException(404, "Repository not found")
    return repo

@app.get("/api/repositories/{repository_id}/branches", response_model=list[Branch])
def list_branches(repository_id: str) -> list[Branch]:
    require_repo(repository_id)
    return list(store.branches[repository_id].values())

@app.post("/api/repositories/{repository_id}/branches", response_model=Branch, status_code=201)
def create_branch(repository_id: str, payload: BranchCreate) -> Branch:
    require_repo(repository_id)
    if payload.from_branch not in store.branches[repository_id]:
        raise HTTPException(400, "Source branch not found")
    if payload.name in store.branches[repository_id]:
        raise HTTPException(409, "Branch already exists")
    source = store.branches[repository_id][payload.from_branch]
    branch = Branch(id=store.new_id(), repository_id=repository_id, name=payload.name, head_commit_id=source.head_commit_id)
    store.branches[repository_id][payload.name] = branch
    store.log("branch.create", f"{repository_id}:{payload.name}")
    return branch

@app.post("/api/repositories/{repository_id}/commits", response_model=Commit, status_code=201)
def create_commit(repository_id: str, payload: CommitCreate) -> Commit:
    require_repo(repository_id)
    branch = store.branches[repository_id].get(payload.branch)
    if not branch:
        raise HTTPException(400, "Branch not found")
    commit = Commit(id=store.new_id(), repository_id=repository_id, **payload.model_dump())
    store.commits[repository_id].append(commit)
    branch.head_commit_id = commit.id
    store.log("commit.create", f"{repository_id}:{commit.id}")
    return commit

@app.get("/api/repositories/{repository_id}/commits", response_model=list[Commit])
def list_commits(repository_id: str) -> list[Commit]:
    require_repo(repository_id)
    return store.commits[repository_id]

@app.post("/api/repositories/{repository_id}/pulls", response_model=PullRequest, status_code=201)
def create_pull(repository_id: str, payload: PullRequestCreate) -> PullRequest:
    require_repo(repository_id)
    branches = store.branches[repository_id]
    if payload.head not in branches or payload.base not in branches:
        raise HTTPException(400, "Head or base branch not found")
    pr = PullRequest(id=store.new_id(), repository_id=repository_id, **payload.model_dump())
    store.pulls[repository_id].append(pr)
    store.log("pull.create", f"{repository_id}:{pr.id}")
    return pr

@app.get("/api/repositories/{repository_id}/pulls", response_model=list[PullRequest])
def list_pulls(repository_id: str) -> list[PullRequest]:
    require_repo(repository_id)
    return store.pulls[repository_id]

@app.post("/api/repositories/{repository_id}/pulls/{pull_id}/review", response_model=PullRequest)
def review_pull(repository_id: str, pull_id: str) -> PullRequest:
    require_repo(repository_id)
    pr = next((p for p in store.pulls[repository_id] if p.id == pull_id), None)
    if not pr:
        raise HTTPException(404, "Pull request not found")
    pr.review_score = 100
    store.log("pull.review", f"{repository_id}:{pull_id}:100")
    return pr

@app.post("/api/repositories/{repository_id}/pulls/{pull_id}/merge", response_model=PullRequest)
def merge_pull(repository_id: str, pull_id: str) -> PullRequest:
    require_repo(repository_id)
    pr = next((p for p in store.pulls[repository_id] if p.id == pull_id), None)
    if not pr:
        raise HTTPException(404, "Pull request not found")
    if pr.review_score != 100:
        raise HTTPException(409, "Pull request requires a passing review")
    pr.status = PullStatus.merged
    store.branches[repository_id][pr.base].head_commit_id = store.branches[repository_id][pr.head].head_commit_id
    store.log("pull.merge", f"{repository_id}:{pull_id}")
    return pr

@app.post("/api/repositories/{repository_id}/actions/run")
def run_action(repository_id: str, branch: str = "main"):
    require_repo(repository_id)
    if branch not in store.branches[repository_id]:
        raise HTTPException(400, "Branch not found")
    return WorkflowService.run(repository_id, branch)

@app.get("/api/repositories/{repository_id}/actions")
def list_actions(repository_id: str):
    require_repo(repository_id)
    return store.runs[repository_id]

@app.post("/api/ai/chat", response_model=AiResponse)
def ai_chat(payload: AiRequest) -> AiResponse:
    answer, actions = AiService.respond(payload.prompt, payload.provider)
    store.log("ai.chat", payload.provider)
    return AiResponse(provider=payload.provider, answer=answer, actions=actions)

@app.get("/api/audit")
def audit():
    return store.audit
