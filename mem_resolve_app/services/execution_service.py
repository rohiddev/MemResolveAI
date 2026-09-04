from typing import Any

from mem_resolve_app.repositories.execution_repository import (
    execute_approval_once,
    find_execution,
)


def execute_approved_action(
    *,
    request_id: str,
    executed_by: str,
) -> dict[str, Any]:
    """Execute an approved claim action."""
    normalized_request_id = request_id.strip()
    normalized_executor = executed_by.strip()

    if not normalized_request_id:
        return {
            "status": "INVALID_REQUEST",
            "message": "request_id is required.",
        }

    if not normalized_executor:
        return {
            "status": "INVALID_REQUEST",
            "message": "executed_by is required.",
        }

    return execute_approval_once(
        request_id=normalized_request_id,
        executed_by=normalized_executor,
    )


def retrieve_execution(
    *,
    request_id: str,
) -> dict[str, Any]:
    """Retrieve an execution record."""
    normalized_request_id = request_id.strip()

    if not normalized_request_id:
        return {
            "status": "INVALID_REQUEST",
            "message": "request_id is required.",
        }

    execution = find_execution(normalized_request_id)

    if execution is None:
        return {
            "status": "NOT_FOUND",
            "request_id": normalized_request_id,
            "message": "No execution record was found.",
        }

    return {
        "status": "FOUND",
        "execution": execution.model_dump(mode="json"),
    }