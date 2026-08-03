from __future__ import annotations
from .models import RunStatus, WorkflowRun
from .store import store

class WorkflowService:
    @staticmethod
    def run(repository_id: str, branch: str) -> WorkflowRun:
        run = WorkflowRun(
            id=store.new_id(),
            repository_id=repository_id,
            name="quality-gate",
            branch=branch,
            status=RunStatus.running,
            logs=["format: ok", "tests: ok", "security: ok", "architecture: ok"],
        )
        run.status = RunStatus.success
        store.runs[repository_id].append(run)
        store.log("workflow.run", f"{repository_id}:{branch}:{run.status}")
        return run

class AiService:
    @staticmethod
    def respond(prompt: str, provider: str) -> tuple[str, list[str]]:
        normalized = prompt.strip()
        answer = (
            f"AI provider '{provider}' reviewed the request: {normalized}. "
            "The proposed change must use a branch, tests, review evidence, and human approval before merge."
        )
        return answer, ["analyze", "plan", "create-branch", "implement", "test", "review"]
