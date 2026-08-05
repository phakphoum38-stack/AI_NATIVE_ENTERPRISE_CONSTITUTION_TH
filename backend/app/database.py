from __future__ import annotations
import json, sqlite3, threading
from contextlib import contextmanager
from pathlib import Path
from .config import settings

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS repositories(id TEXT PRIMARY KEY,name TEXT UNIQUE NOT NULL,description TEXT NOT NULL,remote_url TEXT,default_branch TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS branches(id TEXT PRIMARY KEY,repository_id TEXT NOT NULL,name TEXT NOT NULL,head_commit_id TEXT,created_at TEXT NOT NULL,UNIQUE(repository_id,name),FOREIGN KEY(repository_id) REFERENCES repositories(id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS commits(id TEXT PRIMARY KEY,repository_id TEXT NOT NULL,branch TEXT NOT NULL,parent_commit_id TEXT,message TEXT NOT NULL,files_json TEXT NOT NULL,author TEXT NOT NULL,created_at TEXT NOT NULL,FOREIGN KEY(repository_id) REFERENCES repositories(id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS pulls(id TEXT PRIMARY KEY,repository_id TEXT NOT NULL,title TEXT NOT NULL,body TEXT NOT NULL,head TEXT NOT NULL,base TEXT NOT NULL,status TEXT NOT NULL,review_score INTEGER,required_approvals INTEGER NOT NULL,approvals INTEGER NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,FOREIGN KEY(repository_id) REFERENCES repositories(id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS reviews(id TEXT PRIMARY KEY,pull_id TEXT NOT NULL,reviewer TEXT NOT NULL,decision TEXT NOT NULL,body TEXT NOT NULL,score INTEGER NOT NULL,created_at TEXT NOT NULL,FOREIGN KEY(pull_id) REFERENCES pulls(id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS workflow_runs(id TEXT PRIMARY KEY,repository_id TEXT NOT NULL,name TEXT NOT NULL,branch TEXT NOT NULL,status TEXT NOT NULL,logs_json TEXT NOT NULL,created_at TEXT NOT NULL,finished_at TEXT,FOREIGN KEY(repository_id) REFERENCES repositories(id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS audit_events(id TEXT PRIMARY KEY,action TEXT NOT NULL,subject TEXT NOT NULL,actor TEXT NOT NULL,metadata_json TEXT NOT NULL,created_at TEXT NOT NULL);
"""

class Database:
    def __init__(self,path:str|None=None):
        self.path=Path(path or settings.database_path); self.path.parent.mkdir(parents=True,exist_ok=True); self.lock=threading.RLock(); self.initialize()
    def connect(self):
        c=sqlite3.connect(self.path,check_same_thread=False); c.row_factory=sqlite3.Row; c.execute("PRAGMA foreign_keys=ON"); return c
    def initialize(self):
        with self.connect() as c: c.executescript(SCHEMA)
    @contextmanager
    def transaction(self):
        with self.lock:
            c=self.connect()
            try: yield c; c.commit()
            except Exception: c.rollback(); raise
            finally: c.close()
    def reset(self):
        with self.transaction() as c:
            for t in ("reviews","pulls","workflow_runs","commits","branches","repositories","audit_events"): c.execute(f"DELETE FROM {t}")

db=Database()

def dumps(v): return json.dumps(v,ensure_ascii=False,sort_keys=True)
def loads(v): return json.loads(v or "{}")
