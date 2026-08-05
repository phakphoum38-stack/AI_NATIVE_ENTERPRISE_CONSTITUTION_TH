from __future__ import annotations
from pathlib import Path
from fastapi import Depends,FastAPI,HTTPException,Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlite3 import IntegrityError
from .config import settings
from .models import *
from .repositories import repo
from .security import require_token
from .services import AiService,WorkflowService

app=FastAPI(title="AI Workspaces Model API",version="1.0.0")
app.add_middleware(CORSMiddleware,allow_origins=list(settings.cors_origins),allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
FRONTEND=Path(__file__).resolve().parents[2]/"frontend"
app.mount("/assets",StaticFiles(directory=FRONTEND),name="assets")
@app.get("/",include_in_schema=False)
def index(): return FileResponse(FRONTEND/"index.html")
@app.get("/api/health")
def health(): return {"status":"ok","service":"ai-workspaces-model","version":"1.0.0","environment":settings.environment}

def require_repo(rid):
    value=repo.get_repository(rid)
    if not value: raise HTTPException(404,"Repository not found")
    return value
@app.get("/api/repositories",response_model=Page)
def repositories(limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0),_:str=Depends(require_token)):
    items=[x.model_dump() for x in repo.list_repositories(limit,offset)];return Page(items=items,total=repo.count_repositories(),limit=limit,offset=offset)
@app.post("/api/repositories",response_model=Repository,status_code=201)
def create_repository(p:RepositoryCreate,actor:str=Depends(require_token)):
    try:r=repo.create_repository(p)
    except IntegrityError:raise HTTPException(409,"Repository name already exists")
    repo.audit("repository.create",r.id,actor,{"name":r.name});return r
@app.get("/api/repositories/{rid}",response_model=Repository)
def get_repository(rid:str,_:str=Depends(require_token)):return require_repo(rid)
@app.delete("/api/repositories/{rid}",status_code=204)
def delete_repository(rid:str,actor:str=Depends(require_token)):
    require_repo(rid);repo.delete_repository(rid);repo.audit("repository.delete",rid,actor);return None
@app.get("/api/repositories/{rid}/branches",response_model=list[Branch])
def branches(rid:str,_:str=Depends(require_token)):require_repo(rid);return repo.list_branches(rid)
@app.post("/api/repositories/{rid}/branches",response_model=Branch,status_code=201)
def create_branch(rid:str,p:BranchCreate,actor:str=Depends(require_token)):
    require_repo(rid)
    if not repo.get_branch(rid,p.from_branch):raise HTTPException(400,"Source branch not found")
    if repo.get_branch(rid,p.name):raise HTTPException(409,"Branch already exists")
    b=repo.create_branch(rid,p);repo.audit("branch.create",b.id,actor,{"repository_id":rid,"name":b.name});return b
@app.get("/api/repositories/{rid}/commits",response_model=list[Commit])
def commits(rid:str,branch:str|None=None,_:str=Depends(require_token)):require_repo(rid);return repo.list_commits(rid,branch)
@app.post("/api/repositories/{rid}/commits",response_model=Commit,status_code=201)
def create_commit(rid:str,p:CommitCreate,actor:str=Depends(require_token)):
    require_repo(rid)
    if not repo.get_branch(rid,p.branch):raise HTTPException(400,"Branch not found")
    c=repo.create_commit(rid,p);repo.audit("commit.create",c.id,actor,{"branch":c.branch});return c
@app.get("/api/repositories/{rid}/pulls",response_model=list[PullRequest])
def pulls(rid:str,_:str=Depends(require_token)):require_repo(rid);return repo.list_pulls(rid)
@app.post("/api/repositories/{rid}/pulls",response_model=PullRequest,status_code=201)
def create_pull(rid:str,p:PullRequestCreate,actor:str=Depends(require_token)):
    require_repo(rid)
    if p.head==p.base:raise HTTPException(400,"Head and base must differ")
    if not repo.get_branch(rid,p.head) or not repo.get_branch(rid,p.base):raise HTTPException(400,"Head or base branch not found")
    pr=repo.create_pull(rid,p);repo.audit("pull.create",pr.id,actor);return pr
@app.post("/api/repositories/{rid}/pulls/{pid}/reviews",response_model=PullRequest)
def review(rid:str,pid:str,p:ReviewCreate,actor:str=Depends(require_token)):
    pr=require_repo(rid) and repo.get_pull(rid,pid)
    if not pr:raise HTTPException(404,"Pull request not found")
    if pr.status in (PullStatus.merged,PullStatus.closed):raise HTTPException(409,"Pull request is not reviewable")
    rv,updated=repo.save_review(pr,p);repo.audit("pull.review",pid,actor,{"decision":rv.decision.value,"score":str(rv.score)});return updated
@app.get("/api/repositories/{rid}/pulls/{pid}/reviews",response_model=list[Review])
def reviews(rid:str,pid:str,_:str=Depends(require_token)):
    require_repo(rid)
    if not repo.get_pull(rid,pid):raise HTTPException(404,"Pull request not found")
    return repo.list_reviews(pid)
@app.post("/api/repositories/{rid}/pulls/{pid}/merge",response_model=PullRequest)
def merge(rid:str,pid:str,actor:str=Depends(require_token)):
    pr=require_repo(rid) and repo.get_pull(rid,pid)
    if not pr:raise HTTPException(404,"Pull request not found")
    if pr.status!=PullStatus.approved or pr.approvals<pr.required_approvals or (pr.review_score or 0)<90:raise HTTPException(409,"Pull request has not passed governance gates")
    runs=repo.list_runs(rid)
    if not any(x.branch==pr.head and x.status==RunStatus.success for x in runs):raise HTTPException(409,"Head branch requires a successful workflow run")
    merged=repo.merge_pull(pr);repo.audit("pull.merge",pid,actor);return merged
@app.post("/api/repositories/{rid}/actions",response_model=WorkflowRun,status_code=201)
def run_action(rid:str,p:WorkflowRequest,actor:str=Depends(require_token)):
    require_repo(rid)
    if not repo.get_branch(rid,p.branch):raise HTTPException(400,"Branch not found")
    run=WorkflowService.run(rid,p.branch,p.name);repo.save_run(run);repo.audit("workflow.run",run.id,actor,{"status":run.status.value});return run
@app.get("/api/repositories/{rid}/actions",response_model=list[WorkflowRun])
def actions(rid:str,_:str=Depends(require_token)):require_repo(rid);return repo.list_runs(rid)
@app.post("/api/ai/chat",response_model=AiResponse)
def ai_chat(p:AiRequest,actor:str=Depends(require_token)):
    if p.repository_id:require_repo(p.repository_id)
    try:r=AiService.respond(p)
    except KeyError:raise HTTPException(400,"Unsupported AI provider")
    repo.audit("ai.chat",r.trace_id,actor,{"provider":r.provider,"repository_id":p.repository_id or ""});return r
@app.get("/api/audit",response_model=list[AuditEvent])
def audit(limit:int=Query(100,ge=1,le=500),_:str=Depends(require_token)):return repo.list_audit(limit)
