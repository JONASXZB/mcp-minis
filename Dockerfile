# Glama verification image for mcp-minis.
# Glama builds with the repository root as context. This image packages the
# memory-vault server (pure stdio + SQLite, no network needed at runtime),
# which starts and answers MCP introspection (initialize / tools/list).
FROM python:3.12-slim

WORKDIR /app

COPY servers/memory-vault/ ./

RUN pip install --no-cache-dir .

CMD ["memory-vault"]
