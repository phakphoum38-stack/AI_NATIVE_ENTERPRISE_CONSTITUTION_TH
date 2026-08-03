from __future__ import annotations

from sqlite3 import IntegrityError
from uuid import uuid4

from .database import db, dumps, loads
from .models import *


def uid() -> str:
    return uuid4().hex


class WorkspaceRepository:
    def create_workspace(self, payload: WorkspaceCreate, actor: str) -> Workspace:
        workspace = Workspace(id=uid(), created_by=actor, **payload.model_dump())
        membership = Membership(
            id=uid(),
            workspace_id=workspace.id,
            user_id=actor,
            role=WorkspaceRole.owner,
        )
        with db.transaction() as connection:
            connection.execute(
                "INSERT INTO workspaces VALUES(?,?,?,?,?,?)",
                (
                    workspace.id,
                    workspace.name,
                    workspace.slug,
                    workspace.description,
                    workspace.created_by,
                    workspace.created_at,
                ),
            )
            connection.execute(
                "INSERT INTO memberships VALUES(?,?,?,?,?)",
                (
                    membership.id,
                    membership.workspace_id,
                    membership.user_id,
                    membership.role.value,
                    membership.created_at,
                ),
            )
        return workspace

    def list_workspaces(self, user_id: str) -> list[Workspace]:
        with db.connect() as connection:
            rows = connection.execute(
                """
                SELECT w.* FROM workspaces w
                JOIN memberships m ON m.workspace_id=w.id
                WHERE m.user_id=? ORDER BY w.created_at DESC
                """,
                (user_id,),
            ).fetchall()
        return [Workspace(**dict(row)) for row in rows]

    def get_workspace(self, workspace_id: str) -> Workspace | None:
        with db.connect() as connection:
            row = connection.execute(
                "SELECT * FROM workspaces WHERE id=?", (workspace_id,)
            ).fetchone()
        return Workspace(**dict(row)) if row else None

    def get_membership(self, workspace_id: str, user_id: str) -> Membership | None:
        with db.connect() as connection:
            row = connection.execute(
                "SELECT * FROM memberships WHERE workspace_id=? AND user_id=?",
                (workspace_id, user_id),
            ).fetchone()
        return Membership(**dict(row)) if row else None

    def list_memberships(self, workspace_id: str) -> list[Membership]:
        with db.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM memberships WHERE workspace_id=? ORDER BY created_at",
                (workspace_id,),
            ).fetchall()
        return [Membership(**dict(row)) for row in rows]

    def save_membership(
        self, workspace_id: str, payload: MembershipCreate
    ) -> Membership:
        existing = self.get_membership(workspace_id, payload.user_id)
        if existing:
            with db.transaction() as connection:
                connection.execute(
                    "UPDATE memberships SET role=? WHERE id=?",
                    (payload.role.value, existing.id),
                )
            return existing.model_copy(update={"role": payload.role})
        membership = Membership(
            id=uid(), workspace_id=workspace_id, **payload.model_dump()
        )
        with db.transaction() as connection:
            connection.execute(
                "INSERT INTO memberships VALUES(?,?,?,?,?)",
                (
                    membership.id,
                    membership.workspace_id,
                    membership.user_id,
                    membership.role.value,
                    membership.created_at,
                ),
            )
        return membership

    def remove_membership(self, workspace_id: str, user_id: str) -> bool:
        with db.transaction() as connection:
            return (
                connection.execute(
                    "DELETE FROM memberships WHERE workspace_id=? AND user_id=?",
                    (workspace_id, user_id),
                ).rowcount
                > 0
            )

    def create_repository(self, payload: RepositoryCreate) -> Repository:
        repository = Repository(id=uid(), **payload.model_dump())
        branch = Branch(
            id=uid(), repository_id=repository.id, name=repository.default_branch
        )
        with db.transaction() as connection:
            connection.execute(
                """
                INSERT INTO repositories(
                  id,name,description,remote_url,default_branch,workspace_id,archived,created_at
                ) VALUES(?,?,?,?,?,?,?,?)
                """,
                (
                    repository.id,
                    repository.name,
                    repository.description,
                    repository.remote_url,
                    repository.default_branch,
                    repository.workspace_id,
                    int(repository.archived),
                    repository.created_at,
                ),
            )
            connection.execute(
                """
                INSERT INTO branches(
                  id,repository_id,name,head_commit_id,protected,created_at
                ) VALUES(?,?,?,?,?,?)
                """,
                (
                    branch.id,
                    branch.repository_id,
                    branch.name,
                    branch.head_commit_id,
                    int(branch.protected),
                    branch.created_at,
                ),
            )
        return repository

    def list_repositories(
        self, limit: int = 50, offset: int = 0, workspace_id: str | None = None
    ) -> list[Repository]:
        query = "SELECT * FROM repositories"
        arguments: list[object] = []
        if workspace_id:
            query += " WHERE workspace_id=?"
            arguments.append(workspace_id)
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        arguments.extend((limit, offset))
        with db.connect() as connection:
            rows = connection.execute(query, arguments).fetchall()
        return [self._repository(row) for row in rows]

    def count_repositories(self, workspace_id: str | None = None) -> int:
        query = "SELECT COUNT(*) FROM repositories"
        arguments: tuple[object, ...] = ()
        if workspace_id:
            query += " WHERE workspace_id=?"
            arguments = (workspace_id,)
        with db.connect() as connection:
            return int(connection.execute(query, arguments).fetchone()[0])

    def get_repository(self, repository_id: str) -> Repository | None:
        with db.connect() as connection:
            row = connection.execute(
                "SELECT * FROM repositories WHERE id=?", (repository_id,)
            ).fetchone()
        return self._repository(row) if row else None

    def archive_repository(self, repository_id: str, archived: bool) -> Repository | None:
        with db.transaction() as connection:
            connection.execute(
                "UPDATE repositories SET archived=? WHERE id=?",
                (int(archived), repository_id),
            )
        return self.get_repository(repository_id)

    def delete_repository(self, repository_id: str) -> bool:
        with db.transaction() as connection:
            return (
                connection.execute(
                    "DELETE FROM repositories WHERE id=?", (repository_id,)
                ).rowcount
                > 0
            )

    def list_branches(self, repository_id: str) -> list[Branch]:
        with db.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM branches WHERE repository_id=? ORDER BY name",
                (repository_id,),
            ).fetchall()
        return [self._branch(row) for row in rows]

    def get_branch(self, repository_id: str, name: str) -> Branch | None:
        with db.connect() as connection:
            row = connection.execute(
                "SELECT * FROM branches WHERE repository_id=? AND name=?",
                (repository_id, name),
            ).fetchone()
        return self._branch(row) if row else None

    def create_branch(self, repository_id: str, payload: BranchCreate) -> Branch:
        source = self.get_branch(repository_id, payload.from_branch)
        branch = Branch(
            id=uid(),
            repository_id=repository_id,
            name=payload.name,
            head_commit_id=source.head_commit_id if source else None,
        )
        with db.transaction() as connection:
            connection.execute(
                """
                INSERT INTO branches(
                  id,repository_id,name,head_commit_id,protected,created_at
                ) VALUES(?,?,?,?,?,?)
                """,
                (
                    branch.id,
                    branch.repository_id,
                    branch.name,
                    branch.head_commit_id,
                    int(branch.protected),
                    branch.created_at,
                ),
            )
        return branch

    def protect_branch(
        self, repository_id: str, name: str, protected: bool
    ) -> Branch | None:
        with db.transaction() as connection:
            connection.execute(
                "UPDATE branches SET protected=? WHERE repository_id=? AND name=?",
                (int(protected), repository_id, name),
            )
        return self.get_branch(repository_id, name)

    def create_commit(self, repository_id: str, payload: CommitCreate) -> Commit:
        branch = self.get_branch(repository_id, payload.branch)
        commit = Commit(
            id=uid(),
            repository_id=repository_id,
            parent_commit_id=branch.head_commit_id if branch else None,
            **payload.model_dump(),
        )
        with db.transaction() as connection:
            connection.execute(
                "INSERT INTO commits VALUES(?,?,?,?,?,?,?,?)",
                (
                    commit.id,
                    commit.repository_id,
                    commit.branch,
                    commit.parent_commit_id,
                    commit.message,
                    dumps(commit.files),
                    commit.author,
                    commit.created_at,
                ),
            )
            connection.execute(
                "UPDATE branches SET head_commit_id=? WHERE repository_id=? AND name=?",
                (commit.id, repository_id, payload.branch),
            )
        return commit

    def get_commit(self, repository_id: str, commit_id: str) -> Commit | None:
        with db.connect() as connection:
            row = connection.execute(
                "SELECT * FROM commits WHERE repository_id=? AND id=?",
                (repository_id, commit_id),
            ).fetchone()
        return self._commit(row) if row else None

    def list_commits(
        self, repository_id: str, branch: str | None = None
    ) -> list[Commit]:
        query = "SELECT * FROM commits WHERE repository_id=?"
        arguments: list[object] = [repository_id]
        if branch:
            query += " AND branch=?"
            arguments.append(branch)
        query += " ORDER BY created_at DESC"
        with db.connect() as connection:
            rows = connection.execute(query, arguments).fetchall()
        return [self._commit(row) for row in rows]

    def create_pull(
        self, repository_id: str, payload: PullRequestCreate
    ) -> PullRequest:
        values = payload.model_dump(exclude={"draft"})
        pull = PullRequest(
            id=uid(),
            repository_id=repository_id,
            status=PullStatus.draft if payload.draft else PullStatus.open,
            **values,
        )
        with db.transaction() as connection:
            connection.execute(
                "INSERT INTO pulls VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    pull.id,
                    pull.repository_id,
                    pull.title,
                    pull.body,
                    pull.head,
                    pull.base,
                    pull.status.value,
                    pull.review_score,
                    pull.required_approvals,
                    pull.approvals,
                    pull.created_at,
                    pull.updated_at,
                ),
            )
        return pull

    def get_pull(self, repository_id: str, pull_id: str) -> PullRequest | None:
        with db.connect() as connection:
            row = connection.execute(
                "SELECT * FROM pulls WHERE repository_id=? AND id=?",
                (repository_id, pull_id),
            ).fetchone()
        return PullRequest(**dict(row)) if row else None

    def list_pulls(self, repository_id: str) -> list[PullRequest]:
        with db.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM pulls WHERE repository_id=? ORDER BY created_at DESC",
                (repository_id,),
            ).fetchall()
        return [PullRequest(**dict(row)) for row in rows]

    def save_review(
        self, pull: PullRequest, payload: ReviewCreate
    ) -> tuple[Review, PullRequest]:
        score = round(
            sum(
                (
                    payload.architecture,
                    payload.tests,
                    payload.documentation,
                    payload.security,
                    payload.maintainability,
                    payload.explainability,
                )
            )
            / 6
        )
        review = Review(
            id=uid(),
            pull_id=pull.id,
            reviewer=payload.reviewer,
            decision=payload.decision,
            body=payload.body,
            score=score,
        )
        current = self._reviewer_decision(pull.id, payload.reviewer)
        approvals = pull.approvals
        if current == ReviewDecision.approve:
            approvals -= 1
        if payload.decision == ReviewDecision.approve:
            approvals += 1
        status = pull.status
        if payload.decision == ReviewDecision.request_changes:
            status = PullStatus.changes_requested
        elif approvals >= pull.required_approvals and score >= 90:
            status = PullStatus.approved
        elif pull.status in (PullStatus.approved, PullStatus.changes_requested):
            status = PullStatus.open
        with db.transaction() as connection:
            connection.execute(
                "DELETE FROM reviews WHERE pull_id=? AND reviewer=?",
                (pull.id, payload.reviewer),
            )
            connection.execute(
                "INSERT INTO reviews VALUES(?,?,?,?,?,?,?)",
                (
                    review.id,
                    review.pull_id,
                    review.reviewer,
                    review.decision.value,
                    review.body,
                    review.score,
                    review.created_at,
                ),
            )
            connection.execute(
                """
                UPDATE pulls SET review_score=?,approvals=?,status=?,updated_at=?
                WHERE id=?
                """,
                (score, max(0, approvals), status.value, now_iso(), pull.id),
            )
        updated = self.get_pull(pull.repository_id, pull.id)
        if updated is None:
            raise RuntimeError("Pull request disappeared during review")
        return review, updated

    def list_reviews(self, pull_id: str) -> list[Review]:
        with db.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM reviews WHERE pull_id=? ORDER BY created_at", (pull_id,)
            ).fetchall()
        return [Review(**dict(row)) for row in rows]

    def merge_pull(self, pull: PullRequest) -> PullRequest:
        head = self.get_branch(pull.repository_id, pull.head)
        if head is None:
            raise ValueError("Head branch not found")
        with db.transaction() as connection:
            connection.execute(
                "UPDATE branches SET head_commit_id=? WHERE repository_id=? AND name=?",
                (head.head_commit_id, pull.repository_id, pull.base),
            )
            connection.execute(
                "UPDATE pulls SET status=?,updated_at=? WHERE id=?",
                (PullStatus.merged.value, now_iso(), pull.id),
            )
        merged = self.get_pull(pull.repository_id, pull.id)
        if merged is None:
            raise RuntimeError("Pull request disappeared during merge")
        return merged

    def save_run(self, run: WorkflowRun) -> None:
        with db.transaction() as connection:
            connection.execute(
                "INSERT INTO workflow_runs VALUES(?,?,?,?,?,?,?,?)",
                (
                    run.id,
                    run.repository_id,
                    run.name,
                    run.branch,
                    run.status.value,
                    dumps(run.logs),
                    run.created_at,
                    run.finished_at,
                ),
            )

    def list_runs(self, repository_id: str) -> list[WorkflowRun]:
        with db.connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM workflow_runs WHERE repository_id=?
                ORDER BY created_at DESC
                """,
                (repository_id,),
            ).fetchall()
        return [
            WorkflowRun(
                id=row["id"],
                repository_id=row["repository_id"],
                name=row["name"],
                branch=row["branch"],
                status=row["status"],
                logs=loads(row["logs_json"], []),
                created_at=row["created_at"],
                finished_at=row["finished_at"],
            )
            for row in rows
        ]

    def create_issue(
        self, repository_id: str, payload: IssueCreate, actor: str
    ) -> Issue:
        with db.transaction() as connection:
            number = int(
                connection.execute(
                    "SELECT COALESCE(MAX(number),0)+1 FROM issues WHERE repository_id=?",
                    (repository_id,),
                ).fetchone()[0]
            )
            issue = Issue(
                id=uid(),
                repository_id=repository_id,
                number=number,
                author=actor,
                **payload.model_dump(),
            )
            connection.execute(
                "INSERT INTO issues VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    issue.id,
                    issue.repository_id,
                    issue.number,
                    issue.title,
                    issue.body,
                    issue.status.value,
                    issue.priority.value,
                    issue.author,
                    issue.assignee,
                    dumps(issue.labels),
                    issue.created_at,
                    issue.updated_at,
                ),
            )
        return issue

    def get_issue(self, repository_id: str, number: int) -> Issue | None:
        with db.connect() as connection:
            row = connection.execute(
                "SELECT * FROM issues WHERE repository_id=? AND number=?",
                (repository_id, number),
            ).fetchone()
        return self._issue(row) if row else None

    def list_issues(
        self, repository_id: str, status: IssueStatus | None = None
    ) -> list[Issue]:
        query = "SELECT * FROM issues WHERE repository_id=?"
        arguments: list[object] = [repository_id]
        if status:
            query += " AND status=?"
            arguments.append(status.value)
        query += " ORDER BY number DESC"
        with db.connect() as connection:
            rows = connection.execute(query, arguments).fetchall()
        return [self._issue(row) for row in rows]

    def update_issue(
        self, repository_id: str, number: int, payload: IssueUpdate
    ) -> Issue | None:
        issue = self.get_issue(repository_id, number)
        if issue is None:
            return None
        changes = payload.model_dump(exclude_unset=True)
        updated = issue.model_copy(update={**changes, "updated_at": now_iso()})
        with db.transaction() as connection:
            connection.execute(
                """
                UPDATE issues SET title=?,body=?,status=?,priority=?,assignee=?,
                labels_json=?,updated_at=? WHERE id=?
                """,
                (
                    updated.title,
                    updated.body,
                    updated.status.value,
                    updated.priority.value,
                    updated.assignee,
                    dumps(updated.labels),
                    updated.updated_at,
                    updated.id,
                ),
            )
        return updated

    def add_comment(
        self, subject_type: str, subject_id: str, payload: CommentCreate, actor: str
    ) -> Comment:
        comment = Comment(
            id=uid(),
            subject_type=subject_type,
            subject_id=subject_id,
            author=actor,
            body=payload.body,
        )
        with db.transaction() as connection:
            connection.execute(
                "INSERT INTO comments VALUES(?,?,?,?,?,?,?)",
                (
                    comment.id,
                    comment.subject_type,
                    comment.subject_id,
                    comment.author,
                    comment.body,
                    comment.created_at,
                    comment.updated_at,
                ),
            )
        return comment

    def list_comments(self, subject_type: str, subject_id: str) -> list[Comment]:
        with db.connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM comments WHERE subject_type=? AND subject_id=?
                ORDER BY created_at
                """,
                (subject_type, subject_id),
            ).fetchall()
        return [Comment(**dict(row)) for row in rows]

    def create_label(self, repository_id: str, payload: LabelCreate) -> Label:
        label = Label(id=uid(), repository_id=repository_id, **payload.model_dump())
        with db.transaction() as connection:
            connection.execute(
                "INSERT INTO labels VALUES(?,?,?,?,?,?)",
                (
                    label.id,
                    label.repository_id,
                    label.name,
                    label.color,
                    label.description,
                    label.created_at,
                ),
            )
        return label

    def list_labels(self, repository_id: str) -> list[Label]:
        with db.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM labels WHERE repository_id=? ORDER BY name",
                (repository_id,),
            ).fetchall()
        return [Label(**dict(row)) for row in rows]

    def create_policy(self, repository_id: str, payload: PolicyCreate) -> Policy:
        policy = Policy(id=uid(), repository_id=repository_id, **payload.model_dump())
        with db.transaction() as connection:
            connection.execute(
                "INSERT INTO policies VALUES(?,?,?,?,?,?,?,?)",
                (
                    policy.id,
                    policy.repository_id,
                    policy.name,
                    policy.description,
                    int(policy.enabled),
                    dumps(policy.rules),
                    policy.created_at,
                    policy.updated_at,
                ),
            )
        return policy

    def list_policies(self, repository_id: str) -> list[Policy]:
        with db.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM policies WHERE repository_id=? ORDER BY name",
                (repository_id,),
            ).fetchall()
        return [self._policy(row) for row in rows]

    def create_environment(
        self, repository_id: str, payload: EnvironmentCreate
    ) -> Environment:
        environment = Environment(
            id=uid(), repository_id=repository_id, **payload.model_dump()
        )
        with db.transaction() as connection:
            connection.execute(
                "INSERT INTO environments VALUES(?,?,?,?,?,?)",
                (
                    environment.id,
                    environment.repository_id,
                    environment.name,
                    int(environment.protected),
                    environment.required_approvals,
                    environment.created_at,
                ),
            )
        return environment

    def get_environment(
        self, repository_id: str, name: str
    ) -> Environment | None:
        with db.connect() as connection:
            row = connection.execute(
                "SELECT * FROM environments WHERE repository_id=? AND name=?",
                (repository_id, name),
            ).fetchone()
        return self._environment(row) if row else None

    def list_environments(self, repository_id: str) -> list[Environment]:
        with db.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM environments WHERE repository_id=? ORDER BY name",
                (repository_id,),
            ).fetchall()
        return [self._environment(row) for row in rows]

    def create_deployment(
        self, repository_id: str, payload: DeploymentCreate, actor: str
    ) -> Deployment:
        deployment = Deployment(
            id=uid(), repository_id=repository_id, actor=actor, **payload.model_dump()
        )
        with db.transaction() as connection:
            connection.execute(
                "INSERT INTO deployments VALUES(?,?,?,?,?,?,?,?,?,?)",
                (
                    deployment.id,
                    deployment.repository_id,
                    deployment.environment,
                    deployment.branch,
                    deployment.commit_id,
                    deployment.description,
                    deployment.status.value,
                    deployment.actor,
                    deployment.created_at,
                    deployment.finished_at,
                ),
            )
        return deployment

    def list_deployments(self, repository_id: str) -> list[Deployment]:
        with db.connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM deployments WHERE repository_id=?
                ORDER BY created_at DESC
                """,
                (repository_id,),
            ).fetchall()
        return [Deployment(**dict(row)) for row in rows]

    def notify(
        self,
        recipient: str,
        kind: NotificationKind,
        title: str,
        body: str = "",
        metadata: dict[str, str] | None = None,
    ) -> Notification:
        notification = Notification(
            id=uid(),
            recipient=recipient,
            kind=kind,
            title=title,
            body=body,
            metadata=metadata or {},
        )
        with db.transaction() as connection:
            connection.execute(
                "INSERT INTO notifications VALUES(?,?,?,?,?,?,?,?)",
                (
                    notification.id,
                    notification.recipient,
                    notification.kind.value,
                    notification.title,
                    notification.body,
                    int(notification.read),
                    dumps(notification.metadata),
                    notification.created_at,
                ),
            )
        return notification

    def list_notifications(self, recipient: str) -> list[Notification]:
        with db.connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM notifications WHERE recipient=?
                ORDER BY created_at DESC
                """,
                (recipient,),
            ).fetchall()
        return [
            Notification(
                id=row["id"],
                recipient=row["recipient"],
                kind=row["kind"],
                title=row["title"],
                body=row["body"],
                read=bool(row["read"]),
                metadata=loads(row["metadata_json"], {}),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def mark_notification_read(
        self, notification_id: str, recipient: str
    ) -> bool:
        with db.transaction() as connection:
            return (
                connection.execute(
                    "UPDATE notifications SET read=1 WHERE id=? AND recipient=?",
                    (notification_id, recipient),
                ).rowcount
                > 0
            )

    def audit(
        self,
        action: str,
        subject: str,
        actor: str = "system",
        metadata: dict[str, str] | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            id=uid(),
            action=action,
            subject=subject,
            actor=actor,
            metadata=metadata or {},
        )
        with db.transaction() as connection:
            connection.execute(
                "INSERT INTO audit_events VALUES(?,?,?,?,?,?)",
                (
                    event.id,
                    event.action,
                    event.subject,
                    event.actor,
                    dumps(event.metadata),
                    event.created_at,
                ),
            )
        return event

    def list_audit(self, limit: int = 100) -> list[AuditEvent]:
        with db.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM audit_events ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [
            AuditEvent(
                id=row["id"],
                action=row["action"],
                subject=row["subject"],
                actor=row["actor"],
                metadata=loads(row["metadata_json"], {}),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def _reviewer_decision(
        self, pull_id: str, reviewer: str
    ) -> ReviewDecision | None:
        with db.connect() as connection:
            row = connection.execute(
                "SELECT decision FROM reviews WHERE pull_id=? AND reviewer=?",
                (pull_id, reviewer),
            ).fetchone()
        return ReviewDecision(row["decision"]) if row else None

    @staticmethod
    def _repository(row) -> Repository:
        data = dict(row)
        data["archived"] = bool(data.get("archived", 0))
        return Repository(**data)

    @staticmethod
    def _branch(row) -> Branch:
        data = dict(row)
        data["protected"] = bool(data.get("protected", 0))
        return Branch(**data)

    @staticmethod
    def _commit(row) -> Commit:
        return Commit(
            id=row["id"],
            repository_id=row["repository_id"],
            branch=row["branch"],
            parent_commit_id=row["parent_commit_id"],
            message=row["message"],
            files=loads(row["files_json"], {}),
            author=row["author"],
            created_at=row["created_at"],
        )

    @staticmethod
    def _issue(row) -> Issue:
        return Issue(
            id=row["id"],
            repository_id=row["repository_id"],
            number=row["number"],
            title=row["title"],
            body=row["body"],
            status=row["status"],
            priority=row["priority"],
            author=row["author"],
            assignee=row["assignee"],
            labels=loads(row["labels_json"], []),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _policy(row) -> Policy:
        return Policy(
            id=row["id"],
            repository_id=row["repository_id"],
            name=row["name"],
            description=row["description"],
            enabled=bool(row["enabled"]),
            rules=loads(row["rules_json"], {}),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _environment(row) -> Environment:
        data = dict(row)
        data["protected"] = bool(data["protected"])
        return Environment(**data)


repo = WorkspaceRepository()
