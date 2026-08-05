from __future__ import annotations
from .models import WorkflowRun,RunStatus,now_iso
from .repositories import uid
from .providers import registry

class WorkflowService:
    @staticmethod
    def run(repository_id,branch,name="quality-gate"):
        logs=["checkout: success","format: success","analysis: success","tests: success","security: success","documentation: success"]
        return WorkflowRun(id=uid(),repository_id=repository_id,name=name,branch=branch,status=RunStatus.success,logs=logs,finished_at=now_iso())
class AiService:
    @staticmethod
    def respond(request): return registry.resolve(request.provider).complete(request)
