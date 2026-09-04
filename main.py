import os
from pathlib import Path
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, Request
from google.adk.cli.fast_api import get_fast_api_app

from mem_resolve_app.tool_gateway.context import (
    ToolRequestContext,
    reset_tool_context,
    set_tool_context,
)


PROJECT_ROOT = Path(__file__).resolve().parent

SESSION_SERVICE_URI = os.getenv(
    "SESSION_SERVICE_URI",
    "sqlite+aiosqlite:///./mem_resolve_app/.adk/session.db",
)

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "*").split(",")
    if origin.strip()
]

app: FastAPI = get_fast_api_app(
    agents_dir=str(PROJECT_ROOT),
    session_service_uri=SESSION_SERVICE_URI,
    allow_origins=ALLOWED_ORIGINS,
    web=True,
)


@app.middleware("http")
async def apply_tool_request_context(
    request: Request,
    call_next,
):
    """Apply identity and correlation metadata to agent tool calls."""
    if request.url.path not in {"/run", "/run_sse"}:
        return await call_next(request)

    correlation_id = (
        request.headers.get("X-Correlation-ID")
        or str(uuid4())
    )

    user_id = request.headers.get(
        "X-MemResolve-User-ID",
        "local-development-user",
    ).strip()

    roles = tuple(
        role.strip()
        for role in request.headers.get(
            "X-MemResolve-Roles",
            "provider_ops",
        ).split(",")
        if role.strip()
    )

    context = ToolRequestContext(
        correlation_id=correlation_id,
        user_id=user_id,
        agent_name="resolution_supervisor",
        roles=roles,
    )

    context_token = set_tool_context(context)

    try:
        response = await call_next(request)
    finally:
        reset_tool_context(context_token)

    response.headers["X-Correlation-ID"] = correlation_id

    return response


@app.get("/health")
async def health() -> dict[str, str]:
    """Return the service health status."""
    return {
        "status": "healthy",
        "application": "MemResolve AI",
    }


def main() -> None:
    """Run the MemResolveAI FastAPI application."""
    port = int(os.getenv("PORT", "8080"))

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
    )


if __name__ == "__main__":
    main()