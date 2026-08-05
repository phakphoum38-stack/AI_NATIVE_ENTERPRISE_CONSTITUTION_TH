from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field, field_validator


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class PullStatus(str, Enum):
    draft="draft"; open="open"; approved="approved"; changes_requested="changes_requested"; merged="merged"; closed="closed"
class RunStatus(str, Enum):
    queued="queued"; running="running"; success="success"; failed="failed"; cancelled="cancelled"
class ReviewDecision(str, Enum):
    approve="approve"; request_changes="request_changes"; comment="comment"

class RepositoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9._-]+$")
    description: str = Field(default="", max_length=500)
    remote_url: str | None = None
class Repository(BaseModel):
    id: str; name: str; description: str=""; remote_url: str|None=None; default_branch: str="main"; created_at: str=Field(default_factory=now_iso)
class BranchCreate(BaseModel):
    name: str = Field(min_length=1,max_length=120,pattern=r"^[A-Za-z0-9._/-]+$")
    from_branch: str="main"
class Branch(BaseModel):
    id: str; repository_id: str; name: str; head_commit_id: str|None=None; created_at: str=Field(default_factory=now_iso)
class CommitCreate(BaseModel):
    branch: str; message: str=Field(min_length=1,max_length=300); files: dict[str,str]=Field(default_factory=dict); author: str="AI"
    @field_validator("files")
    @classmethod
    def safe_paths(cls,v):
        for p in v:
            if p.startswith("/") or ".." in p.split("/"): raise ValueError("Unsafe file path")
        return v
class Commit(BaseModel):
    id: str; repository_id: str; branch: str; parent_commit_id: str|None=None; message: str; files: dict[str,str]; author: str; created_at: str=Field(default_factory=now_iso)
class PullRequestCreate(BaseModel):
    title: str=Field(min_length=1,max_length=200); body: str=Field(default="",max_length=5000); head: str; base: str="main"; draft: bool=False
class PullRequest(BaseModel):
    id: str; repository_id: str; title: str; body: str=""; head: str; base: str; status: PullStatus=PullStatus.open; review_score: int|None=None; required_approvals: int=1; approvals: int=0; created_at: str=Field(default_factory=now_iso); updated_at: str=Field(default_factory=now_iso)
class ReviewCreate(BaseModel):
    reviewer: str=Field(min_length=1,max_length=120); decision: ReviewDecision; body: str=Field(default="",max_length=4000); architecture: int=Field(ge=0,le=100,default=100); tests: int=Field(ge=0,le=100,default=100); documentation: int=Field(ge=0,le=100,default=100); security: int=Field(ge=0,le=100,default=100); maintainability: int=Field(ge=0,le=100,default=100); explainability: int=Field(ge=0,le=100,default=100)
class Review(BaseModel):
    id: str; pull_id: str; reviewer: str; decision: ReviewDecision; body: str=""; score: int; created_at: str=Field(default_factory=now_iso)
class WorkflowRequest(BaseModel):
    branch: str="main"; name: str="quality-gate"
class WorkflowRun(BaseModel):
    id: str; repository_id: str; name: str; branch: str; status: RunStatus=RunStatus.queued; logs: list[str]=Field(default_factory=list); created_at: str=Field(default_factory=now_iso); finished_at: str|None=None
class AiRequest(BaseModel):
    prompt: str=Field(min_length=1,max_length=12000); provider: str="mock"; model: str|None=None; repository_id: str|None=None; context: dict[str,str]=Field(default_factory=dict)
class AiResponse(BaseModel):
    provider: str; model: str; answer: str; actions: list[str]=Field(default_factory=list); trace_id: str
class AuditEvent(BaseModel):
    id: str; action: str; subject: str; actor: str="system"; metadata: dict[str,str]=Field(default_factory=dict); created_at: str=Field(default_factory=now_iso)
class Page(BaseModel):
    items: list[dict]; total: int; limit: int; offset: int
