# AI Workspaces Model

Governance-first GitHub-like AI development workspace. It is a standalone platform and does not contain Shift Calendar code.

## Implemented

- Persistent SQLite repositories, branches, commits, pull requests, reviews, workflow runs and audit events
- Bearer-token API protection
- PR governance gates: approval score, required approvals and successful workflow on the head branch
- AI provider registry with a safe mock provider and extension point for external providers
- GitHub-like browser dashboard
- Docker, health check, OpenAPI and automated tests

## Run

```bash
cp .env.example .env
docker compose up --build
```

Open `http://localhost:8000`. Default development token: `dev-token-change-me`.

## Test

```bash
cd backend
python -m pip install -r requirements.txt
pytest -q
```
