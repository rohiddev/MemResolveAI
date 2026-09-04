FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PORT=8080

ENV SESSION_SERVICE_URI=sqlite+aiosqlite:////tmp/memresolve/session.db

WORKDIR /app
RUN mkdir -p /tmp/memresolve

COPY pyproject.toml uv.lock ./

RUN uv sync \
    --frozen \
    --no-dev \
    --group local-rag \
    --no-install-project

COPY mem_resolve_app ./mem_resolve_app
COPY mem_resolve_mcp ./mem_resolve_mcp
COPY scripts ./scripts
COPY data/policies ./data/policies
COPY main.py ./

RUN uv sync \
    --frozen \
    --no-dev \
    --group local-rag

# Settings requires a project value during module initialization.
# Indexing itself is local and does not call Vertex AI.
RUN GOOGLE_CLOUD_PROJECT=container-build \
    GOOGLE_GENAI_USE_VERTEXAI=true \
    KNOWLEDGE_BACKEND=chroma \
    CHROMA_PERSIST_DIRECTORY=data/chroma \
    uv run --no-sync python -m scripts.index_chroma

EXPOSE 8080

CMD ["sh", "-c", "uv run --no-sync uvicorn main:app --host 0.0.0.0 --port ${PORT}"]