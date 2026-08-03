from __future__ import annotations

from pathlib import Path
from sqlite3 import IntegrityError

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .models import *
from .repositories import repo
from .security import (
    require_repository_role,
    require_token,
    require_workspace_role,
)
from .services import AiService, WorkflowService


app = FastAPI(title="AI Workspaces Model API", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
FRONTEND = Path(__file__).resolve().parents[2] / "frontend"
app.mount("/assets", StaticFiles(directory=FRONTEND), name="assets")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(FRONTEND / "index.html")


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "ai-workspaces-model",
        "version": "2.0.0",
        "environment": settings.environment,
    }


def require_repo(repository_id: str) -> Repository:
    value = repo.get_repository(repository_id)
    if value is None:
        raise HTTPException(404, "Repository not found")
    return value


def require_workspace(workspace_id: str) -> Workspace:
    value = repo.get_workspace(workspace_id)
    if value is None:
        raise HTTPException(404, "Workspace not found")
    return value


@app.get("/api/workspaces", response_model=list[Workspace])
def workspaces(actor: str = Depends(require_token)):
    return repo.list_workspaces(actor)


@app.post("/api/workspaces", response_model=Workspace, status_code=201)
def create_workspace(payload: WorkspaceCreate, actor: str = Depends(require_token)):
    try:
        workspace = repo.create_workspace(payload, actor)
    except IntegrityError:
        raise HTTPException(409, "Workspace slug already exists")
    repo.audit("workspace.create", workspace.id, actor, {"slug": workspace.slug})
    return workspace


@app.get("/api/workspaces/{workspace_id}", response_model=Workspace)
def get_workspace(workspace_id: str, actor: str = Depends(require_token)):
    workspace = require_workspace(workspace_id)
    require_workspace_role(workspace_id, actor, WorkspaceRole.viewer)
    return workspace


@app.get(
    "/api/workspaces/{workspace_id}/members", response_model=list[Membership]
)
def memberships(workspace_id: str, actor: str = Depends(require_token)):
    require_workspace(workspace_id)
    require_workspace_role(workspace_id, actor, WorkspaceRole.viewer)
    return repo.list_memberships(workspace_id)


@app.put(
    "/api/workspaces/{workspace_id}/members/{user_id}",
    response_model=Membership,
)
def save_membership(
    workspace_id: str,
    user_id: str,
    payload: MembershipCreate,
    actor: str = Depends(require_token),
):
    require_workspace(workspace_id)
    require_workspace_role(workspace_id, actor, WorkspaceRole.admin)
    if payload.user_id != user_id:
        raise HTTPException(400, "Path user and payload user must match")
    membership = repo.save_membership(workspace_id, payload)
    repo.audit(
        "workspace.member.save",
        membership.id,
        actor,
        {"workspace_id": workspace_id, "user_id": user_id, "role": membership.role.value},
    )
    return membership


@app.delete("/api/workspaces/{workspace_id}/members/{user_id}", status_code=204)
def remove_membership(
    workspace_id: str,
    user_id: str,
    actor: str = Depends(require_token),
):
    require_workspace(workspace_id)
    require_workspace_role(workspace_id, actor, WorkspaceRole.admin)
    membership = repo.get_membership(workspace_id, user_id)
    if membership is None:
        raise HTTPException(404, "Membership not found")
    if membership.role == WorkspaceRole.owner:
        raise HTTPException(409, "Workspace owner cannot be removed")
    repo.remove_membership(workspace_id, user_id)
    repo.audit(
        "workspace.member.remove",
        membership.id,
        actor,
        {"workspace_id": workspace_id, "user_id": user_id},
    )
    return None


@app.get("/api/repositories", response_model=Page)
def repositories(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    workspace_id: str | None = None,
    actor: str = Depends(require_token),
):
    if workspace_id:
        require_workspace_role(workspace_id, actor, WorkspaceRole.viewer)
    items = [
        item.model_dump()
        for item in repo.list_repositories(limit, offset, workspace_id)
    ]
    return Page(
        items=items,
        total=repo.count_repositories(workspace_id),
        limit=limit,
        offset=offset,
    )


@app.post("/api/repositories", response_model=Repository, status_code=201)
def create_repository(
    payload: RepositoryCreate, actor: str = Depends(require_token)
):
    if payload.workspace_id:
        require_workspace(payload.workspace_id)
        require_workspace_role(
            payload.workspace_id, actor, WorkspaceRole.maintainer
        )
    try:
        repository = repo.create_repository(payload)
    except IntegrityError:
        raise HTTPException(409, "Repository name already exists")
    repo.audit("repository.create", repository.id, actor, {"name": repository.name})
    return repository


@app.get("/api/repositories/{repository_id}", response_model=Repository)
def get_repository(repository_id: str, actor: str = Depends(require_token)):
    require_repository_role(repository_id, actor, WorkspaceRole.viewer)
    return require_repo(repository_id)


@app.post("/api/repositories/{repository_id}/archive", response_model=Repository)
def archive_repository(
    repository_id: str,
    archived: bool = True,
    actor: str = Depends(require_token),
):
    require_repository_role(repository_id, actor, WorkspaceRole.admin)
    updated = repo.archive_repository(repository_id, archived)
    if updated is None:
        raise HTTPException(404, "Repository not found")
    repo.audit(
        "repository.archive",
        repository_id,
        actor,
        {"archived": str(archived).lower()},
    )
    return updated


@app.delete("/api/repositories/{repository_id}", status_code=204)
def delete_repository(repository_id: str, actor: str = Depends(require_token)):
    require_repository_role(repository_id, actor, WorkspaceRole.admin)
    require_repo(repository_id)
    repo.delete_repository(repository_id)
    repo.audit("repository.delete", repository_id, actor)
    return None


@app.get(
    "/api/repositories/{repository_id}/branches", response_model=list[Branch]
)
def branches(repository_id: str, actor: str = Depends(require_token)):
    require_repository_role(repository_id, actor, WorkspaceRole.viewer)
    return repo.list_branches(repository_id)


@app.post(
    "/api/repositories/{repository_id}/branches",
    response_model=Branch,
    status_code=201,
)
def create_branch(
    repository_id: str,
    payload: BranchCreate,
    actor: str = Depends(require_token),
):
    require_repository_role(repository_id, actor, WorkspaceRole.developer)
    if not repo.get_branch(repository_id, payload.from_branch):
        raise HTTPException(400, "Source branch not found")
    if repo.get_branch(repository_id, payload.name):
        raise HTTPException(409, "Branch already exists")
    branch = repo.create_branch(repository_id, payload)
    repo.audit(
        "branch.create",
        branch.id,
        actor,
        {"repository_id": repository_id, "name": branch.name},
    )
    return branch


@app.put(
    "/api/repositories/{repository_id}/branches/{branch_name}/protection",
    response_model=Branch,
)
def protect_branch(
    repository_id: str,
    branch_name: str,
    protected: bool = True,
    actor: str = Depends(require_token),
):
    require_repository_role(repository_id, actor, WorkspaceRole.maintainer)
    branch = repo.protect_branch(repository_id, branch_name, protected)
    if branch is None:
        raise HTTPException(404, "Branch not found")
    repo.audit(
        "branch.protection",
        branch.id,
        actor,
        {"protected": str(protected).lower()},
    )
    return branch


@app.get(
    "/api/repositories/{repository_id}/commits", response_model=list[Commit]
)
def commits(
    repository_id: str,
    branch: str | None = None,
    actor: str = Depends(require_token),
):
    require_repository_role(repository_id, actor, WorkspaceRole.viewer)
    return repo.list_commits(repository_id, branch)


@app.post(
    "/api/repositories/{repository_id}/commits",
    response_model=Commit,
    status_code=201,
)
def create_commit(
    repository_id: str,
    payload: CommitCreate,
    actor: str = Depends(require_token),
):
    require_repository_role(repository_id, actor, WorkspaceRole.developer)
    branch = repo.get_branch(repository_id, payload.branch)
    if branch is None:
        raise HTTPException(400, "Branch not found")
    if branch.protected:
        raise HTTPException(409, "Direct commits to protected branches are disabled")
    commit = repo.create_commit(repository_id, payload.model_copy(update={"author": actor}))
    repo.audit("commit.create", commit.id, actor, {"branch": commit.branch})
    return commit


@app.get(
    "/api/repositories/{repository_id}/pulls", response_model=list[PullRequest]
)
def pulls(repository_id: str, actor: str = Depends(require_token)):
    require_repository_role(repository_id, actor, WorkspaceRole.viewer)
    return repo.list_pulls(repository_id)


@app.post(
    "/api/repositories/{repository_id}/pulls",
    response_model=PullRequest,
    status_code=201,
)
def create_pull(
    repository_id: str,
    payload: PullRequestCreate,
    actor: str = Depends(require_token),
):
    require_repository_role(repository_id, actor, WorkspaceRole.developer)
    if payload.head == payload.base:
        raise HTTPException(400, "Head and base must differ")
    if not repo.get_branch(repository_id, payload.head) or not repo.get_branch(
        repository_id, payload.base
    ):
        raise HTTPException(400, "Head or base branch not found")
    pull = repo.create_pull(repository_id, payload)
    repo.audit("pull.create", pull.id, actor)
    return pull


@app.post(
    "/api/repositories/{repository_id}/pulls/{pull_id}/reviews",
    response_model=PullRequest,
)
def review(
    repository_id: str,
    pull_id: str,
    payload: ReviewCreate,
    actor: str = Depends(require_token),
):
    require_repository_role(repository_id, actor, WorkspaceRole.reviewer)
    pull = repo.get_pull(repository_id, pull_id)
    if pull is None:
        raise HTTPException(404, "Pull request not found")
    if pull.status in (PullStatus.merged, PullStatus.closed):
        raise HTTPException(409, "Pull request is not reviewable")
    review_payload = payload.model_copy(update={"reviewer": actor})
    saved, updated = repo.save_review(pull, review_payload)
    repo.audit(
        "pull.review",
        pull_id,
        actor,
        {"decision": saved.decision.value, "score": str(saved.score)},
    )
    return updated


@app.get(
    "/api/repositories/{repository_id}/pulls/{pull_id}/reviews",
    response_model=list[Review],
)
def reviews(
    repository_id: str,
    pull_id: str,
    actor: str = Depends(require_token),
):
    require_repository_role(repository_id, actor, WorkspaceRole.viewer)
    if not repo.get_pull(repository_id, pull_id):
        raise HTTPException(404, "Pull request not found")
    return repo.list_reviews(pull_id)


@app.post(
    "/api/repositories/{repository_id}/pulls/{pull_id}/merge",
    response_model=PullRequest,
)
def merge(
    repository_id: str,
    pull_id: str,
    actor: str = Depends(require_token),
):
    require_repository_role(repository_id, actor, WorkspaceRole.maintainer)
    pull = repo.get_pull(repository_id, pull_id)
    if pull is None:
        raise HTTPException(404, "Pull request not found")
    if (
        pull.status != PullStatus.approved
        or pull.approvals < pull.required_approvals
        or (pull.review_score or 0) < 90
    ):
        raise HTTPException(409, "Pull request has not passed governance gates")
    runs = repo.list_runs(repository_id)
    if not any(
        run.branch == pull.head and run.status == RunStatus.success for run in runs
    ):
        raise HTTPException(409, "Head branch requires a successful workflow run")
    merged = repo.merge_pull(pull)
    repo.audit("pull.merge", pull_id, actor)
    return merged


@app.post(
    "/api/repositories/{repository_id}/actions",
    response_model=WorkflowRun,
    status_code=201,
)
def run_action(
    repository_id: str,
    payload: WorkflowRequest,
    actor: str = Depends(require_token),
):
    require_repository_role(repository_id, actor, WorkspaceRole.developer)
    if not repo.get_branch(repository_id, payload.branch):
        raise HTTPException(400, "Branch not found")
    run = WorkflowService.run(repository_id, payload.branch, payload.name)
    repo.save_run(run)
    repo.audit("workflow.run", run.id, actor, {"status": run.status.value})
    return run


@app.get(
    "/api/repositories/{repository_id}/actions", response_model=list[WorkflowRun]
)
def actions(repository_id: str, actor: str = Depends(require_token)):
    require_repository_role(repository_id, actor, WorkspaceRole.viewer)
    return repo.list_runs(repository_id)


@app.get(
    "/api/repositories/{repository_id}/issues", response_model=list[Issue]
)
def issues(
    repository_id: str,
    status: IssueStatus | None = None,
    actor: str = Depends(require_token),
):
    require_repository_role(repository_id, actor, WorkspaceRole.viewer)
    return repo.list_issues(repository_id, status)


@app.post(
    "/api/repositories/{repository_id}/issues",
    response_model=Issue,
    status_code=201,
)
def create_issue(
    repository_id: str,
    payload: IssueCreate,
    actor: str = Depends(require_token),
):
    require_repository_role(repository_id, actor, WorkspaceRole.developer)
    issue = repo.create_issue(repository_id, payload, actor)
    repo.audit("issue.create", issue.id, actor, {"number": str(issue.number)})
    if issue.assignee:
        repo.notify(
            issue.assignee,
            NotificationKind.action_required,
            f"Issue #{issue.number} assigned to you",
            issue.title,
            {"repository_id": repository_id, "issue_id": issue.id},
        )
    return issue


@app.get(
    "/api/repositories/{repository_id}/issues/{number}", response_model=Issue
)
def get_issue(
    repository_id: str,
    number: int,
    actor: str = Depends(require_token),
):
    require_repository_role(repository_id, actor, WorkspaceRole.viewer)
    issue = repo.get_issue(repository_id, number)
    if issue is None:
        raise HTTPException(404, "Issue not found")
    return issue


@app.patch(
    "/api/repositories/{repository_id}/issues/{number}", response_model=Issue
)
def update_issue(
    repository_id: str,
    number: int,
    payload: IssueUpdate,
    actor: str = Depends(require_token),
):
    require_repository_role(repository_id, actor, WorkspaceRole.developer)
    issue = repo.update_issue(repository_id, number, payload)
    if issue is None:
        raise HTTPException(404, "Issue not found")
    repo.audit("issue.update", issue.id, actor, {"status": issue.status.value})
    return issue


@app.get(
    "/api/repositories/{repository_id}/issues/{number}/comments",
    response_model=list[Comment],
)
def issue_comments(
    repository_id: str,
    number: int,
    actor: str = Depends(require_token),
):
    require_repository_role(repository_id, actor, WorkspaceRole.viewer)
    issue = repo.get_issue(repository_id, number)
    if issue is None:
        raise HTTPException(404, "Issue not found")
    return repo.list_comments("issue", issue.id)


@app.post(
    "/api/repositories/{repository_id}/issues/{number}/comments",
    response_model=Comment,
    status_code=201,
)
def add_issue_comment(
    repository_id: str,
    number: int,
    payload: CommentCreate,
    actor: str = Depends(require_token),
):
    require_repository_role(repository_id, actor, WorkspaceRole.developer)
    issue = repo.get_issue(repository_id, number)
    if issue is None:
        raise HTTPException(404, "Issue not found")
    comment = repo.add_comment("issue", issue.id, payload, actor)
    repo.audit("issue.comment", issue.id, actor, {"comment_id": comment.id})
    return comment


@app.get(
    "/api/repositories/{repository_id}/labels", response_model=list[Label]
)
def labels(repository_id: str, actor: str = Depends(require_token)):
    require_repository_role(repository_id, actor, WorkspaceRole.viewer)
    return repo.list_labels(repository_id)


@app.post(
    "/api/repositories/{repository_id}/labels",
    response_model=Label,
    status_code=201,
)
def create_label(
    repository_id: str,
    payload: LabelCreate,
    actor: str = Depends(require_token),
):
    require_repository_role(repository_id, actor, WorkspaceRole.maintainer)
    try:
        label = repo.create_label(repository_id, payload)
    except IntegrityError:
        raise HTTPException(409, "Label already exists")
    repo.audit("label.create", label.id, actor, {"name": label.name})
    return label


@app.get(
    "/api/repositories/{repository_id}/policies", response_model=list[Policy]
)
def policies(repository_id: str, actor: str = Depends(require_token)):
    require_repository_role(repository_id, actor, WorkspaceRole.viewer)
    return repo.list_policies(repository_id)


@app.post(
    "/api/repositories/{repository_id}/policies",
    response_model=Policy,
    status_code=201,
)
def create_policy(
    repository_id: str,
    payload: PolicyCreate,
    actor: str = Depends(require_token),
):
    require_repository_role(repository_id, actor, WorkspaceRole.maintainer)
    try:
        policy = repo.create_policy(repository_id, payload)
    except IntegrityError:
        raise HTTPException(409, "Policy already exists")
    repo.audit("policy.create", policy.id, actor, {"name": policy.name})
    return policy


@app.get(
    "/api/repositories/{repository_id}/environments",
    response_model=list[Environment],
)
def environments(repository_id: str, actor: str = Depends(require_token)):
    require_repository_role(repository_id, actor, WorkspaceRole.viewer)
    return repo.list_environments(repository_id)


@app.post(
    "/api/repositories/{repository_id}/environments",
    response_model=Environment,
    status_code=201,
)
def create_environment(
    repository_id: str,
    payload: EnvironmentCreate,
    actor: str = Depends(require_token),
):
    require_repository_role(repository_id, actor, WorkspaceRole.maintainer)
    try:
        environment = repo.create_environment(repository_id, payload)
    except IntegrityError:
        raise HTTPException(409, "Environment already exists")
    repo.audit(
        "environment.create",
        environment.id,
        actor,
        {"name": environment.name},
    )
    return environment


@app.get(
    "/api/repositories/{repository_id}/deployments",
    response_model=list[Deployment],
)
def deployments(repository_id: str, actor: str = Depends(require_token)):
    require_repository_role(repository_id, actor, WorkspaceRole.viewer)
    return repo.list_deployments(repository_id)


@app.post(
    "/api/repositories/{repository_id}/deployments",
    response_model=Deployment,
    status_code=201,
)
def create_deployment(
    repository_id: str,
    payload: DeploymentCreate,
    actor: str = Depends(require_token),
):
    require_repository_role(repository_id, actor, WorkspaceRole.maintainer)
    environment = repo.get_environment(repository_id, payload.environment)
    if environment is None:
        raise HTTPException(400, "Environment not found")
    if not repo.get_branch(repository_id, payload.branch):
        raise HTTPException(400, "Branch not found")
    if payload.commit_id and not repo.get_commit(repository_id, payload.commit_id):
        raise HTTPException(400, "Commit not found")
    if environment.protected and environment.required_approvals > 0:
        raise HTTPException(
            409,
            "Protected environment requires an approval workflow before deployment",
        )
    deployment = repo.create_deployment(repository_id, payload, actor)
    repo.audit(
        "deployment.create",
        deployment.id,
        actor,
        {"environment": deployment.environment, "branch": deployment.branch},
    )
    return deployment


@app.get("/api/notifications", response_model=list[Notification])
def notifications(actor: str = Depends(require_token)):
    return repo.list_notifications(actor)


@app.post("/api/notifications/{notification_id}/read", status_code=204)
def mark_notification_read(
    notification_id: str,
    actor: str = Depends(require_token),
):
    if not repo.mark_notification_read(notification_id, actor):
        raise HTTPException(404, "Notification not found")
    return None


@app.post("/api/ai/chat", response_model=AiResponse)
def ai_chat(payload: AiRequest, actor: str = Depends(require_token)):
    if payload.repository_id:
        require_repository_role(
            payload.repository_id, actor, WorkspaceRole.developer
        )
    try:
        response = AiService.respond(payload)
    except KeyError:
        raise HTTPException(400, "Unsupported AI provider")
    repo.audit(
        "ai.chat",
        response.trace_id,
        actor,
        {
            "provider": response.provider,
            "repository_id": payload.repository_id or "",
        },
    )
    return response


@app.get("/api/audit", response_model=list[AuditEvent])
def audit(
    limit: int = Query(100, ge=1, le=500),
    _: str = Depends(require_token),
):
    return repo.list_audit(limit)
