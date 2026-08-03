from __future__ import annotations
from collections import defaultdict
from threading import RLock
from uuid import uuid4
from .models import Branch, Commit, PullRequest, Repository, WorkflowRun

class Store:
    def __init__(self) -> None:
        self.lock = RLock()
        self.repositories: dict[str, Repository] = {}
        self.branches: dict[str, dict[str, Branch]] = defaultdict(dict)
        self.commits: dict[str, list[Commit]] = defaultdict(list)
        self.pulls: dict[str, list[PullRequest]] = defaultdict(list)
        self.runs: dict[str, list[WorkflowRun]] = defaultdict(list)
        self.audit: list[dict[str, str]] = []

    @staticmethod
    def new_id() -> str:
        return uuid4().hex

    def log(self, action: str, detail: str) -> None:
        self.audit.append({"id": self.new_id(), "action": action, "detail": detail})

store = Store()
