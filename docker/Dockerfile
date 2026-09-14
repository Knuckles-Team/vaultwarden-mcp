# syntax=docker/dockerfile:1
# Two runtime images from ONE Dockerfile, selected by build --target. Both are
# multi-stage builds that ship only the installed runtime:
#
#   --target agent  (DEFAULT)  installs vaultwarden-mcp[agent] = the agent runtime
#                              (agent-utilities[agent-runtime,logfire]: engine + agent +
#                              skills). Because [agent] also includes [mcp], this image
#                              can run either the agent or the MCP server. Publish and
#                              deploy it by immutable manifest digest.
#
#   --target mcp               installs vaultwarden-mcp[mcp] = the MCP serving runtime.
#                              The mandatory epistemic-graph[full] engine remains present;
#                              only the optional agent orchestration stack is omitted.
#
#   docker build --target agent -t vaultwarden-mcp:local .
#   docker build --target mcp   -t vaultwarden-mcp:mcp    .
# See agent-packages/CLAUDE.md "Connector recipe" for the tag contract.
FROM python:3.12-slim@sha256:57cd7c3a7a273101a6485ba99423ee568157882804b1124b4dd04266317710de AS builder-base
COPY --from=ghcr.io/astral-sh/uv:0.11.7@sha256:240fb85ab0f263ef12f492d8476aa3a2e4e1e333f7d67fbdd923d00a506a516a /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_SYSTEM_PYTHON=1 \
    UV_HTTP_TIMEOUT=3600
# A few transitive deps ship no manylinux wheel and build from sdist, needing a C++
# toolchain. Install it in the builder only — final stages copy just /usr/local.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# MCP serving dependency closure (including mandatory epistemic-graph[full]).
FROM builder-base AS builder-mcp
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system --upgrade --break-system-packages --prerelease=allow vaultwarden-mcp[mcp]>=0.1.0

# Full agent runtime dependency closure.
FROM builder-base AS builder-agent
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system --upgrade --break-system-packages --prerelease=allow vaultwarden-mcp[agent]>=0.1.0

FROM python:3.12-slim@sha256:57cd7c3a7a273101a6485ba99423ee568157882804b1124b4dd04266317710de AS runtime-base
ARG HOST=127.0.0.1
ARG PORT=8000
ARG TRANSPORT="stdio"
ARG AUTH_TYPE="none"
ENV HOST=${HOST} \
    PORT=${PORT} \
    TRANSPORT=${TRANSPORT} \
    AUTH_TYPE=${AUTH_TYPE} \
    PYTHONUNBUFFERED=1 \
    PATH="/root/.local/bin:/usr/local/bin:${PATH}" \
    UV_HTTP_TIMEOUT=3600 \
    UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# MCP serving image.
FROM runtime-base AS mcp
COPY --from=builder-mcp /usr/local /usr/local
CMD ["vaultwarden-mcp"]

# Agent image (DEFAULT target); can also run the MCP server.
FROM runtime-base AS agent
COPY --from=builder-agent /usr/local /usr/local
CMD ["vaultwarden-agent"]
