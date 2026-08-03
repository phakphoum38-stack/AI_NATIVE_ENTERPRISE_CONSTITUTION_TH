from __future__ import annotations

from fastapi import Header, HTTPException

from .config import settings
from .models import WorkspaceRole
from .repositories import repo


ROLE_RANK = {
    WorkspaceRole.viewer: 10,
    WorkspaceRole.reviewer: 20,
    WorkspaceRole.developer: 30,
    WorkspaceRole.maintainer: 40,
    WorkspaceRole.admin: 50,
    WorkspaceRole.owner: 60,
}


def require_token(
    authorization: str | None = Header(default=None),
    x_actor: str | None = Header(default=None, alias="X-Actor"),
) -> str:
    expected = f"Bearer {settings.api_token}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing API token")
    actor = (x_actor or "api-user").strip()
    if not actor or len(actor) > 160:
        raise HTTPException(status_code=400, detail="Invalid actor identity")
    return actor


def require_workspace_role(
    workspace_id: str,
    actor: str,
    minimum: WorkspaceRole,
) -> None:
    membership = repo.get_membership(workspace_id, actor)
    if membership is None:
        raise HTTPException(status_code=403, detail="Workspace membership required")
    if ROLE_RANK[membership.role] < ROLE_RANK[minimum]:
        raise HTTPException(
            status_code=403,
            detail=f"Workspace role {minimum.value} or higher is required",
        )


def require_repository_role(
    repository_id: str,
    actor: str,
    minimum: WorkspaceRole,
) -> None:
    repository = repo.get_repository(repository_id)
    if repository is None:
        raise HTTPException(status_code=404, detail="Repository not found")
    if repository.workspace_id is None:
        return
    require_workspace_role(repository.workspace_id, actor, minimum)
