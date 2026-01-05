# Development Workflow

- Always use MCP Sequentialthinking. Research → Plan → Implement (don't jump straight to coding).
- Follow coding rules in [.agent/rules/coding.md](/.agent/rules/coding.md).
- Prefer simple, obvious solutions over clever abstractions.
- Always use `uv` as the package manager.
- After completing changes: run `uv run pytest`.
- If tests fail: stop, investigate, fix, and re-run tests.
- Do not proceed with further implementation until current implementation passes all checks.
- Do not modify `uv.lock` manually; use `uv` commands.
