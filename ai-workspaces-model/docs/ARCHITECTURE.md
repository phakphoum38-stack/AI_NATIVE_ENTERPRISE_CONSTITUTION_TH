# Architecture

- Frontend: static GitHub-like dashboard
- API: FastAPI
- Domain: Repository, Branch, Commit, Pull Request, Workflow Run, AI Request
- Store: thread-safe in-memory implementation for MVP
- Governance: review score is required before merge
- Extension path: persistent database, OAuth, real Git provider, queue runner, provider adapters
