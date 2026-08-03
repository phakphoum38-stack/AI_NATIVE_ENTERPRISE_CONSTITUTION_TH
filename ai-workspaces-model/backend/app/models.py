from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class PullStatus(str, Enum):
    draft = "draft"
    open = "open"
    approved = "approved"
    changes_requested = "changes_requested"
    merged = "merged"
    closed = "closed"


class RunStatus(str, Enum):
    queued = "queued"
    running = "running"
    success = "success"
    failed = "failed"
    cancelled = "cancelled"


class ReviewDecision(str, Enum):
    approve = "approve"
    request_changes = "request_changes"
    comment = "comment"


class WorkspaceRole(str, Enum):
    owner = "owner"
    admin = "admin"
    maintainer = "maintainer"
    developer = "developer"
    reviewer = "reviewer"
    viewer = "viewer"


class IssueStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    blocked = "blocked"
    resolved = "resolved"
    closed = "closed"


class IssuePriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class DeploymentStatus(str, Enum):
    queued = "queued"
    running = "running"
    success = "success"
    failed = "failed"
    cancelled = "cancelled"


class NotificationKind(str, Enum):
    info = "info"
    warning = "warning"
    action_required = "action_required"
    success = "success"


class RepositoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9._-]+$")
    description: str = Field(default="", max_length=500)
    remote_url: str | None = None
    workspace_id: str | None = None


class Repository(BaseModel):
    id: str
    name: str
    description: str = ""
    remote_url: str | None = None
    default_branch: str = "main"
    workspace_id: str | None = None
    archived: bool = False
    created_at: str = Field(default_factory=now_iso)


class BranchCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9._/-]+$")
    from_branch: str = "main"


class Branch(BaseModel):
    id: str
    repository_id: str
    name: str
    head_commit_id: str | None = None
    protected: bool = False
    created_at: str = Field(default_factory=now_iso)


class CommitCreate(BaseModel):
    branch: str
    message: str = Field(min_length=1, max_length=300)
    files: dict[str, str] = Field(default_factory=dict)
    author: str = "AI"

    @field_validator("files")
    @classmethod
    def safe_paths(cls, value: dict[str, str]) -> dict[str, str]:
        for path in value:
            if path.startswith("/") or ".." in path.split("/"):
                raise ValueError("Unsafe file path")
        return value


class Commit(BaseModel):
    id: str
    repository_id: str
    branch: str
    parent_commit_id: str | None = None
    message: str
    files: dict[str, str]
    author: str
    created_at: str = Field(default_factory=now_iso)


class PullRequestCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(default="", max_length=5000)
    head: str
    base: str = "main"
    draft: bool = False
    required_approvals: int = Field(default=1, ge=1, le=20)


class PullRequest(BaseModel):
    id: str
    repository_id: str
    title: str
    body: str = ""
    head: str
    base: str
    status: PullStatus = PullStatus.open
    review_score: int | None = None
    required_approvals: int = 1
    approvals: int = 0
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)


class ReviewCreate(BaseModel):
    reviewer: str = Field(min_length=1, max_length=120)
    decision: ReviewDecision
    body: str = Field(default="", max_length=4000)
    architecture: int = Field(ge=0, le=100, default=100)
    tests: int = Field(ge=0, le=100, default=100)
    documentation: int = Field(ge=0, le=100, default=100)
    security: int = Field(ge=0, le=100, default=100)
    maintainability: int = Field(ge=0, le=100, default=100)
    explainability: int = Field(ge=0, le=100, default=100)


class Review(BaseModel):
    id: str
    pull_id: str
    reviewer: str
    decision: ReviewDecision
    body: str = ""
    score: int
    created_at: str = Field(default_factory=now_iso)


class WorkflowRequest(BaseModel):
    branch: str = "main"
    name: str = "quality-gate"


class WorkflowRun(BaseModel):
    id: str
    repository_id: str
    name: str
    branch: str
    status: RunStatus = RunStatus.queued
    logs: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=now_iso)
    finished_at: str | None = None


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    slug: str = Field(min_length=1, max_length=80, pattern=r"^[a-z0-9-]+$")
    description: str = Field(default="", max_length=500)


class Workspace(BaseModel):
    id: str
    name: str
    slug: str
    description: str = ""
    created_by: str
    created_at: str = Field(default_factory=now_iso)


class MembershipCreate(BaseModel):
    user_id: str = Field(min_length=1, max_length=160)
    role: WorkspaceRole = WorkspaceRole.developer


class Membership(BaseModel):
    id: str
    workspace_id: str
    user_id: str
    role: WorkspaceRole
    created_at: str = Field(default_factory=now_iso)


class IssueCreate(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    body: str = Field(default="", max_length=12000)
    priority: IssuePriority = IssuePriority.medium
    assignee: str | None = Field(default=None, max_length=160)
    labels: list[str] = Field(default_factory=list)


class IssueUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=240)
    body: str | None = Field(default=None, max_length=12000)
    status: IssueStatus | None = None
    priority: IssuePriority | None = None
    assignee: str | None = Field(default=None, max_length=160)
    labels: list[str] | None = None


class Issue(BaseModel):
    id: str
    repository_id: str
    number: int
    title: str
    body: str = ""
    status: IssueStatus = IssueStatus.open
    priority: IssuePriority = IssuePriority.medium
    author: str
    assignee: str | None = None
    labels: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=12000)


class Comment(BaseModel):
    id: str
    subject_type: str
    subject_id: str
    author: str
    body: str
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)


class LabelCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    color: str = Field(default="6b7280", pattern=r"^[0-9A-Fa-f]{6}$")
    description: str = Field(default="", max_length=240)


class Label(BaseModel):
    id: str
    repository_id: str
    name: str
    color: str
    description: str = ""
    created_at: str = Field(default_factory=now_iso)


class PolicyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=1000)
    enabled: bool = True
    rules: dict[str, Any] = Field(default_factory=dict)


class Policy(BaseModel):
    id: str
    repository_id: str
    name: str
    description: str = ""
    enabled: bool = True
    rules: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=now_iso)
    updated_at: str = Field(default_factory=now_iso)


class EnvironmentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9._-]+$")
    protected: bool = False
    required_approvals: int = Field(default=0, ge=0, le=20)


class Environment(BaseModel):
    id: str
    repository_id: str
    name: str
    protected: bool = False
    required_approvals: int = 0
    created_at: str = Field(default_factory=now_iso)


class DeploymentCreate(BaseModel):
    environment: str
    branch: str = "main"
    commit_id: str | None = None
    description: str = Field(default="", max_length=1000)


class Deployment(BaseModel):
    id: str
    repository_id: str
    environment: str
    branch: str
    commit_id: str | None = None
    description: str = ""
    status: DeploymentStatus = DeploymentStatus.queued
    actor: str
    created_at: str = Field(default_factory=now_iso)
    finished_at: str | None = None


class Notification(BaseModel):
    id: str
    recipient: str
    kind: NotificationKind
    title: str
    body: str = ""
    read: bool = False
    metadata: dict[str, str] = Field(default_factory=dict)
    created_at: str = Field(default_factory=now_iso)


class AiRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=12000)
    provider: str = "mock"
    model: str | None = None
    repository_id: str | None = None
    context: dict[str, str] = Field(default_factory=dict)


class AiResponse(BaseModel):
    provider: str
    model: str
    answer: str
    actions: list[str] = Field(default_factory=list)
    trace_id: str


class AuditEvent(BaseModel):
    id: str
    action: str
    subject: str
    actor: str = "system"
    metadata: dict[str, str] = Field(default_factory=dict)
    created_at: str = Field(default_factory=now_iso)


class Page(BaseModel):
    items: list[dict[str, Any]]
    total: int
    limit: int
    offset: int
