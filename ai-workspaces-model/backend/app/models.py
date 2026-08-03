from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class PullStatus(str, Enum):
    open = "open"
    merged = "merged"
    closed = "closed"

class RunStatus(str, Enum):
    queued = "queued"
    running = "running"
    success = "success"
    failed = "failed"

class RepositoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = ""

class Repository(BaseModel):
    id: str
    name: str
    description: str = ""
    default_branch: str = "main"
    created_at: str = Field(default_factory=now_iso)

class BranchCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    from_branch: str = "main"

class Branch(BaseModel):
    id: str
    repository_id: str
    name: str
    head_commit_id: str | None = None
    created_at: str = Field(default_factory=now_iso)

class CommitCreate(BaseModel):
    branch: str
    message: str = Field(min_length=1)
    files: dict[str, str] = Field(default_factory=dict)
    author: str = "AI"

class Commit(BaseModel):
    id: str
    repository_id: str
    branch: str
    message: str
    files: dict[str, str]
    author: str
    created_at: str = Field(default_factory=now_iso)

class PullRequestCreate(BaseModel):
    title: str = Field(min_length=1)
    body: str = ""
    head: str
    base: str = "main"

class PullRequest(BaseModel):
    id: str
    repository_id: str
    title: str
    body: str = ""
    head: str
    base: str
    status: PullStatus = PullStatus.open
    review_score: int | None = None
    created_at: str = Field(default_factory=now_iso)

class WorkflowRun(BaseModel):
    id: str
    repository_id: str
    name: str
    branch: str
    status: RunStatus = RunStatus.queued
    logs: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=now_iso)

class AiRequest(BaseModel):
    prompt: str = Field(min_length=1)
    provider: str = "mock"
    repository_id: str | None = None

class AiResponse(BaseModel):
    provider: str
    answer: str
    actions: list[str] = Field(default_factory=list)
