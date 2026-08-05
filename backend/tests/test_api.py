def create_repo(client,headers,name="demo"):
    r=client.post("/api/repositories",headers=headers,json={"name":name,"description":"x"});assert r.status_code==201;return r.json()
def test_auth_required(client): assert client.get("/api/repositories").status_code==401
def test_repository_crud_and_pagination(client,headers):
    rid=create_repo(client,headers)["id"]
    page=client.get("/api/repositories?limit=10",headers=headers).json();assert page["total"]==1
    assert client.get(f"/api/repositories/{rid}",headers=headers).status_code==200
    assert client.delete(f"/api/repositories/{rid}",headers=headers).status_code==204
def test_duplicate_repository(client,headers):
    create_repo(client,headers);assert client.post("/api/repositories",headers=headers,json={"name":"demo"}).status_code==409
def test_complete_governed_flow(client,headers):
    rid=create_repo(client,headers)["id"]
    assert client.post(f"/api/repositories/{rid}/branches",headers=headers,json={"name":"feat/api"}).status_code==201
    commit=client.post(f"/api/repositories/{rid}/commits",headers=headers,json={"branch":"feat/api","message":"add api","files":{"backend/app.py":"print('ok')"}});assert commit.status_code==201
    pr=client.post(f"/api/repositories/{rid}/pulls",headers=headers,json={"title":"Add API","head":"feat/api"}).json()
    assert client.post(f"/api/repositories/{rid}/pulls/{pr['id']}/merge",headers=headers).status_code==409
    run=client.post(f"/api/repositories/{rid}/actions",headers=headers,json={"branch":"feat/api"});assert run.json()["status"]=="success"
    reviewed=client.post(f"/api/repositories/{rid}/pulls/{pr['id']}/reviews",headers=headers,json={"reviewer":"lead","decision":"approve"});assert reviewed.json()["status"]=="approved"
    merged=client.post(f"/api/repositories/{rid}/pulls/{pr['id']}/merge",headers=headers);assert merged.json()["status"]=="merged"
def test_change_request_blocks_merge(client,headers):
    rid=create_repo(client,headers)["id"];client.post(f"/api/repositories/{rid}/branches",headers=headers,json={"name":"feat/x"});pr=client.post(f"/api/repositories/{rid}/pulls",headers=headers,json={"title":"x","head":"feat/x"}).json()
    r=client.post(f"/api/repositories/{rid}/pulls/{pr['id']}/reviews",headers=headers,json={"reviewer":"r","decision":"request_changes","security":50});assert r.json()["status"]=="changes_requested"
def test_ai_provider_and_audit(client,headers):
    r=client.post("/api/ai/chat",headers=headers,json={"prompt":"review architecture and tests","provider":"mock"});assert r.status_code==200;assert "architecture_review" in r.json()["actions"]
    audit=client.get("/api/audit",headers=headers).json();assert audit[0]["action"]=="ai.chat"
def test_rejects_unsafe_paths(client,headers):
    rid=create_repo(client,headers)["id"];r=client.post(f"/api/repositories/{rid}/commits",headers=headers,json={"branch":"main","message":"bad","files":{"../secret":"x"}});assert r.status_code==422
