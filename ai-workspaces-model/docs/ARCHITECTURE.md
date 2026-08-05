# Architecture

The API uses explicit layers: HTTP routes → services → repository → SQLite. Domain models are Pydantic contracts shared by OpenAPI and validation.

## Governance flow

1. Create repository and branch.
2. Commit an explicit file map.
3. Open a pull request.
4. Run the quality workflow against the head branch.
5. Submit a scored human or AI-assisted review.
6. Merge only when approval, score and workflow gates pass.

## Extension points

- `AiProvider` for OpenAI, Anthropic, Gemini or local models.
- `WorkspaceRepository` can be replaced by PostgreSQL-backed persistence.
- `WorkflowService` can dispatch containers, GitHub Actions or external runners.
- Remote repository metadata is stored without embedding credentials.
