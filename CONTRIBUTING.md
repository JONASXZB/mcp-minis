# Contributing to mcp-minis

Thanks for your interest! Bug fixes, docs improvements, and brand-new minis are all welcome.

## House rules for every server

A mini earns its place in this repo by following five rules:

1. **One job.** Each server does a single, clearly-defined thing.
2. **Free data, no API keys.** If it needs a key, a signup, or a paid tier, it doesn't belong here.
3. **Minimal dependencies.** The official `mcp` SDK plus at most one or two libraries that do the real work.
4. **Graceful errors.** Tools never crash the server — failures return a clear, human-readable error string.
5. **Readable in one sitting.** A single `server.py` module with type hints and a docstring on every tool.

## Adding a new mini server

Create `servers/<your-server>/` with this layout (copy an existing server as your template):

```
servers/<your-server>/
├── pyproject.toml        # hatchling build, [project.scripts] entry point named after the server
├── README.md             # what it does, tool table, install + config snippets, example prompts
├── src/
│   └── <your_package>/
│       ├── __init__.py
│       └── server.py     # FastMCP app; every tool typed + docstringed
└── tests/
    └── test_smoke.py     # at minimum: tool registration + input-validation tests (no network)
```

Checklist before opening the PR:

- [ ] `pyproject.toml` declares `mcp>=1.2` plus only the libraries the server truly needs.
- [ ] The console entry point in `[project.scripts]` matches the server/directory name.
- [ ] The README follows the same shape as the existing servers' READMEs.
- [ ] The server is added to the table in the root `README.md` and to both files in `examples/`.
- [ ] `pytest` passes inside the server directory.
- [ ] You ran the server once through a real MCP client (or an initialize + tools/list exchange) and confirmed the tools show up.

## Development setup

```bash
git clone https://github.com/JONASXZB/mcp-minis.git
cd mcp-minis/servers/<server>
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Style

- Python ≥ 3.10, `from __future__ import annotations` where generics need it.
- No comments that restate the code; do explain *why* when something is non-obvious.
- Keep user-facing strings plain and specific — an error should tell the caller what went wrong and, when possible, what to try instead.
