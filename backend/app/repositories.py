from __future__ import annotations
from uuid import uuid4
from .database import db,dumps,loads
from .models import *

def uid()->str: return uuid4().hex
class WorkspaceRepository:
    def create_repository(self,p:RepositoryCreate)->Repository:
        r=Repository(id=uid(),**p.model_dump()); b=Branch(id=uid(),repository_id=r.id,name="main")
        with db.transaction() as c:
            c.execute("INSERT INTO repositories VALUES(?,?,?,?,?,?)",(r.id,r.name,r.description,r.remote_url,r.default_branch,r.created_at))
            c.execute("INSERT INTO branches VALUES(?,?,?,?,?)",(b.id,b.repository_id,b.name,b.head_commit_id,b.created_at))
        return r
    def list_repositories(self,limit=50,offset=0):
        with db.connect() as c: rows=c.execute("SELECT * FROM repositories ORDER BY created_at DESC LIMIT ? OFFSET ?",(limit,offset)).fetchall()
        return [Repository(**dict(x)) for x in rows]
    def count_repositories(self):
        with db.connect() as c:return c.execute("SELECT COUNT(*) FROM repositories").fetchone()[0]
    def get_repository(self,rid):
        with db.connect() as c:r=c.execute("SELECT * FROM repositories WHERE id=?",(rid,)).fetchone()
        return Repository(**dict(r)) if r else None
    def delete_repository(self,rid):
        with db.transaction() as c:return c.execute("DELETE FROM repositories WHERE id=?",(rid,)).rowcount>0
    def list_branches(self,rid):
        with db.connect() as c: rows=c.execute("SELECT * FROM branches WHERE repository_id=? ORDER BY name",(rid,)).fetchall()
        return [Branch(**dict(x)) for x in rows]
    def get_branch(self,rid,name):
        with db.connect() as c:r=c.execute("SELECT * FROM branches WHERE repository_id=? AND name=?",(rid,name)).fetchone()
        return Branch(**dict(r)) if r else None
    def create_branch(self,rid,p:BranchCreate):
        src=self.get_branch(rid,p.from_branch); b=Branch(id=uid(),repository_id=rid,name=p.name,head_commit_id=src.head_commit_id if src else None)
        with db.transaction() as c:c.execute("INSERT INTO branches VALUES(?,?,?,?,?)",(b.id,b.repository_id,b.name,b.head_commit_id,b.created_at))
        return b
    def create_commit(self,rid,p:CommitCreate):
        b=self.get_branch(rid,p.branch); cm=Commit(id=uid(),repository_id=rid,parent_commit_id=b.head_commit_id if b else None,**p.model_dump())
        with db.transaction() as c:
            c.execute("INSERT INTO commits VALUES(?,?,?,?,?,?,?,?)",(cm.id,cm.repository_id,cm.branch,cm.parent_commit_id,cm.message,dumps(cm.files),cm.author,cm.created_at))
            c.execute("UPDATE branches SET head_commit_id=? WHERE repository_id=? AND name=?",(cm.id,rid,p.branch))
        return cm
    def list_commits(self,rid,branch=None):
        q="SELECT * FROM commits WHERE repository_id=?"; args=[rid]
        if branch:q+=" AND branch=?";args.append(branch)
        q+=" ORDER BY created_at DESC"
        with db.connect() as c:rows=c.execute(q,args).fetchall()
        return [Commit(id=x['id'],repository_id=x['repository_id'],branch=x['branch'],parent_commit_id=x['parent_commit_id'],message=x['message'],files=loads(x['files_json']),author=x['author'],created_at=x['created_at']) for x in rows]
    def create_pull(self,rid,p:PullRequestCreate):
        pr=PullRequest(id=uid(),repository_id=rid,status=PullStatus.draft if p.draft else PullStatus.open,**p.model_dump(exclude={'draft'}))
        with db.transaction() as c:c.execute("INSERT INTO pulls VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(pr.id,pr.repository_id,pr.title,pr.body,pr.head,pr.base,pr.status.value,pr.review_score,pr.required_approvals,pr.approvals,pr.created_at,pr.updated_at))
        return pr
    def get_pull(self,rid,pid):
        with db.connect() as c:r=c.execute("SELECT * FROM pulls WHERE repository_id=? AND id=?",(rid,pid)).fetchone()
        return PullRequest(**dict(r)) if r else None
    def list_pulls(self,rid):
        with db.connect() as c:rows=c.execute("SELECT * FROM pulls WHERE repository_id=? ORDER BY created_at DESC",(rid,)).fetchall()
        return [PullRequest(**dict(x)) for x in rows]
    def save_review(self,pr:PullRequest,p:ReviewCreate):
        score=round(sum([p.architecture,p.tests,p.documentation,p.security,p.maintainability,p.explainability])/6); rv=Review(id=uid(),pull_id=pr.id,reviewer=p.reviewer,decision=p.decision,body=p.body,score=score)
        approvals=pr.approvals+(1 if p.decision==ReviewDecision.approve else 0); status=PullStatus.changes_requested if p.decision==ReviewDecision.request_changes else (PullStatus.approved if approvals>=pr.required_approvals and score>=90 else pr.status)
        with db.transaction() as c:
            c.execute("INSERT INTO reviews VALUES(?,?,?,?,?,?,?)",(rv.id,rv.pull_id,rv.reviewer,rv.decision.value,rv.body,rv.score,rv.created_at))
            c.execute("UPDATE pulls SET review_score=?,approvals=?,status=?,updated_at=? WHERE id=?",(score,approvals,status.value,now_iso(),pr.id))
        return rv,self.get_pull(pr.repository_id,pr.id)
    def list_reviews(self,pid):
        with db.connect() as c:rows=c.execute("SELECT * FROM reviews WHERE pull_id=? ORDER BY created_at",(pid,)).fetchall()
        return [Review(**dict(x)) for x in rows]
    def merge_pull(self,pr):
        head=self.get_branch(pr.repository_id,pr.head)
        with db.transaction() as c:
            c.execute("UPDATE branches SET head_commit_id=? WHERE repository_id=? AND name=?",(head.head_commit_id,pr.repository_id,pr.base))
            c.execute("UPDATE pulls SET status=?,updated_at=? WHERE id=?",(PullStatus.merged.value,now_iso(),pr.id))
        return self.get_pull(pr.repository_id,pr.id)
    def save_run(self,r):
        with db.transaction() as c:c.execute("INSERT INTO workflow_runs VALUES(?,?,?,?,?,?,?,?)",(r.id,r.repository_id,r.name,r.branch,r.status.value,dumps(r.logs),r.created_at,r.finished_at))
    def list_runs(self,rid):
        with db.connect() as c:rows=c.execute("SELECT * FROM workflow_runs WHERE repository_id=? ORDER BY created_at DESC",(rid,)).fetchall()
        return [WorkflowRun(id=x['id'],repository_id=x['repository_id'],name=x['name'],branch=x['branch'],status=x['status'],logs=loads(x['logs_json']),created_at=x['created_at'],finished_at=x['finished_at']) for x in rows]
    def audit(self,action,subject,actor="system",metadata=None):
        e=AuditEvent(id=uid(),action=action,subject=subject,actor=actor,metadata=metadata or {})
        with db.transaction() as c:c.execute("INSERT INTO audit_events VALUES(?,?,?,?,?,?)",(e.id,e.action,e.subject,e.actor,dumps(e.metadata),e.created_at))
        return e
    def list_audit(self,limit=100):
        with db.connect() as c:rows=c.execute("SELECT * FROM audit_events ORDER BY created_at DESC LIMIT ?",(limit,)).fetchall()
        return [AuditEvent(id=x['id'],action=x['action'],subject=x['subject'],actor=x['actor'],metadata=loads(x['metadata_json']),created_at=x['created_at']) for x in rows]
repo=WorkspaceRepository()
