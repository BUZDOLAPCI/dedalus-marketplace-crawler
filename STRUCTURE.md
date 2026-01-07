# Project Structure

## Essential Files (Required for Dedalus)

```
.
├── pyproject.toml      # Package configuration and dependencies
├── main.py             # Entry point (Dedalus runs `uv run main`)
└── src/
    └── main.py         # MCP server entry point
```

## Notes

- The Dedalus entry point is `main.py`, which wraps `src/main.py`.
- Configuration can be provided via `.env.local` (optional) based on `config/.env.example`.
