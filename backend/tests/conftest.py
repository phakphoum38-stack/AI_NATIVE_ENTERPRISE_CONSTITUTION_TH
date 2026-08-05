import os,tempfile
os.environ["DATABASE_PATH"]=tempfile.mktemp(suffix=".db")
os.environ["API_TOKEN"]="test-token"
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import db
@pytest.fixture(autouse=True)
def clean(): db.reset();yield
@pytest.fixture
def client(): return TestClient(app)
@pytest.fixture
def headers(): return {"Authorization":"Bearer test-token"}
