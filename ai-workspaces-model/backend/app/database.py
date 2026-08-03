from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path

from .config import settings


SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS workspaces(
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  description TEXT NOT NULL,
  created_by TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS memberships(
  id TEXT PRIMARY KEY,
  workspace_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  role TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(workspace_id,user_id),
  FOREIGN KEY(workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS repositories(
  id TEXT PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  description TEXT NOT NULL,
  remote_url TEXT,
  default_branch TEXT NOT NULL,
  workspace_id TEXT,
  archived INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  FOREIGN KEY(workspace_id) REFERENCES workspaces(id) ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS branches(
  id TEXT PRIMARY KEY,
  repository_id TEXT NOT NULL,
  name TEXT NOT NULL,
  head_commit_id TEXT,
  protected INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  UNIQUE(repository_id,name),
  FOREIGN KEY(repository_id) REFERENCES repositories(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS commits(
  id TEXT PRIMARY KEY,
  repository_id TEXT NOT NULL,
  branch TEXT NOT NULL,
  parent_commit_id TEXT,
  message TEXT NOT NULL,
  files_json TEXT NOT NULL,
  author TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(repository_id) REFERENCES repositories(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS pulls(
  id TEXT PRIMARY KEY,
  repository_id TEXT NOT NULL,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  head TEXT NOT NULL,
  base TEXT NOT NULL,
  status TEXT NOT NULL,
  review_score INTEGER,
  required_approvals INTEGER NOT NULL,
  approvals INTEGER NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY(repository_id) REFERENCES repositories(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS reviews(
  id TEXT PRIMARY KEY,
  pull_id TEXT NOT NULL,
  reviewer TEXT NOT NULL,
  decision TEXT NOT NULL,
  body TEXT NOT NULL,
  score INTEGER NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(pull_id) REFERENCES pulls(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS workflow_runs(
  id TEXT PRIMARY KEY,
  repository_id TEXT NOT NULL,
  name TEXT NOT NULL,
  branch TEXT NOT NULL,
  status TEXT NOT NULL,
  logs_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  finished_at TEXT,
  FOREIGN KEY(repository_id) REFERENCES repositories(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS issues(
  id TEXT PRIMARY KEY,
  repository_id TEXT NOT NULL,
  number INTEGER NOT NULL,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  status TEXT NOT NULL,
  priority TEXT NOT NULL,
  author TEXT NOT NULL,
  assignee TEXT,
  labels_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(repository_id,number),
  FOREIGN KEY(repository_id) REFERENCES repositories(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS comments(
  id TEXT PRIMARY KEY,
  subject_type TEXT NOT NULL,
  subject_id TEXT NOT NULL,
  author TEXT NOT NULL,
  body TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS labels(
  id TEXT PRIMARY KEY,
  repository_id TEXT NOT NULL,
  name TEXT NOT NULL,
  color TEXT NOT NULL,
  description TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(repository_id,name),
  FOREIGN KEY(repository_id) REFERENCES repositories(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS policies(
  id TEXT PRIMARY KEY,
  repository_id TEXT NOT NULL,
  name TEXT NOT NULL,
  description TEXT NOT NULL,
  enabled INTEGER NOT NULL,
  rules_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(repository_id,name),
  FOREIGN KEY(repository_id) REFERENCES repositories(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS environments(
  id TEXT PRIMARY KEY,
  repository_id TEXT NOT NULL,
  name TEXT NOT NULL,
  protected INTEGER NOT NULL,
  required_approvals INTEGER NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(repository_id,name),
  FOREIGN KEY(repository_id) REFERENCES repositories(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS deployments(
  id TEXT PRIMARY KEY,
  repository_id TEXT NOT NULL,
  environment TEXT NOT NULL,
  branch TEXT NOT NULL,
  commit_id TEXT,
  description TEXT NOT NULL,
  status TEXT NOT NULL,
  actor TEXT NOT NULL,
  created_at TEXT NOT NULL,
  finished_at TEXT,
  FOREIGN KEY(repository_id) REFERENCES repositories(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS notifications(
  id TEXT PRIMARY KEY,
  recipient TEXT NOT NULL,
  kind TEXT NOT NULL,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  read INTEGER NOT NULL,
  metadata_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_events(
  id TEXT PRIMARY KEY,
  action TEXT NOT NULL,
  subject TEXT NOT NULL,
  actor TEXT NOT NULL,
  metadata_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_memberships_user ON memberships(user_id);
CREATE INDEX IF NOT EXISTS idx_repositories_workspace ON repositories(workspace_id);
CREATE INDEX IF NOT EXISTS idx_issues_repository_status ON issues(repository_id,status);
CREATE INDEX IF NOT EXISTS idx_comments_subject ON comments(subject_type,subject_id);
CREATE INDEX IF NOT EXISTS idx_deployments_repository ON deployments(repository_id,created_at);
CREATE INDEX IF NOT EXISTS idx_notifications_recipient ON notifications(recipient,read,created_at);
"""


class Database:
    def __init__(self, path: str | None = None):
        self.path = Path(path or settings.database_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.initialize()

    def connect(self):
        connection = sqlite3.connect(self.path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def initialize(self):
        with self.connect() as connection:
            connection.executescript(SCHEMA)
            self._migrate_legacy_schema(connection)

    def _migrate_legacy_schema(self, connection: sqlite3.Connection) -> None:
        migrations = {
            "repositories": (
                ("workspace_id", "TEXT"),
                ("archived", "INTEGER NOT NULL DEFAULT 0"),
            ),
            "branches": (("protected", "INTEGER NOT NULL DEFAULT 0"),),
        }
        for table, columns in migrations.items():
            existing = {
                row[1]
                for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
            }
            for name, definition in columns:
                if name not in existing:
                    connection.execute(
                        f"ALTER TABLE {table} ADD COLUMN {name} {definition}"
                    )

    @contextmanager
    def transaction(self):
        with self.lock:
            connection = self.connect()
            try:
                yield connection
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                connection.close()

    def reset(self):
        tables = (
            "comments",
            "reviews",
            "pulls",
            "workflow_runs",
            "deployments",
            "environments",
            "policies",
            "labels",
            "issues",
            "commits",
            "branches",
            "repositories",
            "memberships",
            "workspaces",
            "notifications",
            "audit_events",
        )
        with self.transaction() as connection:
            for table in tables:
                connection.execute(f"DELETE FROM {table}")


db = Database()


def dumps(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def loads(value, default=None):
    if value in (None, ""):
        return {} if default is None else default
    return json.loads(value)
