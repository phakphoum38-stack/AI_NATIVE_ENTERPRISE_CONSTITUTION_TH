from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_full_workspace_flow():
    repo = client.post('/api/repositories', json={'name':'demo','description':'x'}).json()
    rid = repo['id']
    assert client.post(f'/api/repositories/{rid}/branches', json={'name':'feat/a'}).status_code == 201
    commit = client.post(f'/api/repositories/{rid}/commits', json={
        'branch':'feat/a','message':'add api','files':{'a.txt':'hello'}
    })
    assert commit.status_code == 201
    pr = client.post(f'/api/repositories/{rid}/pulls', json={'title':'Add API','head':'feat/a'}).json()
    assert client.post(f"/api/repositories/{rid}/pulls/{pr['id']}/merge").status_code == 409
    assert client.post(f"/api/repositories/{rid}/pulls/{pr['id']}/review").json()['review_score'] == 100
    assert client.post(f"/api/repositories/{rid}/pulls/{pr['id']}/merge").json()['status'] == 'merged'
    assert client.post(f'/api/repositories/{rid}/actions/run?branch=main').json()['status'] == 'success'

def test_ai_chat():
    r = client.post('/api/ai/chat', json={'prompt':'review architecture','provider':'mock'})
    assert r.status_code == 200
    assert 'reviewed the request' in r.json()['answer']
