import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app


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


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "healthy",
        "application": "MemResolve AI",
    }


def main() -> None:
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
    )


if __name__ == "__main__":
    main()