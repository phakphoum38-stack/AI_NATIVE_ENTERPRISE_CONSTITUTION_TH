from __future__ import annotations
from abc import ABC, abstractmethod
from uuid import uuid4
from .models import AiRequest,AiResponse

class AiProvider(ABC):
    name: str
    @abstractmethod
    def complete(self,request:AiRequest)->AiResponse: ...
class MockProvider(AiProvider):
    name="mock"
    def complete(self,request):
        actions=[]
        lower=request.prompt.lower()
        if "review" in lower: actions.append("architecture_review")
        if "test" in lower: actions.append("test_plan")
        if "commit" in lower: actions.append("prepare_commit")
        return AiResponse(provider=self.name,model=request.model or "mock-enterprise-v1",answer=f"AI reviewed the request: {request.prompt}",actions=actions,trace_id=uuid4().hex)
class ProviderRegistry:
    def __init__(self):self._providers={"mock":MockProvider()}
    def register(self,p):self._providers[p.name]=p
    def resolve(self,name):
        if name not in self._providers: raise KeyError(name)
        return self._providers[name]
registry=ProviderRegistry()
