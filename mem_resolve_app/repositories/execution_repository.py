from datetime import UTC, datetime
from typing import Any

from google.cloud import firestore

from mem_resolve_app.models.approval import (
    ApprovalRequest,
    ApprovalStatus,
)
from mem_resolve_app.models.execution import (
    ExecutionRecord,
    ExecutionStatus,
)
from mem_resolve_app.repositories.firestore_client import (
    get_firestore_client,
)


APPROVAL_COLLECTION = "memresolve_approval_requests"
EXECUTION_COLLECTION = "memresolve_execution_records"


def execute_approval_once(
    *,
    request_id: str,
    executed_by: str,
) -> dict[str, Any]:
    """Atomically execute an approved request exactly once."""
    client = get_firestore_client()

    approval_reference = client.collection(
        APPROVAL_COLLECTION
    ).document(request_id)

    # The approval request ID is also used as the execution document
    # ID. This provides a natural idempotency key.
    execution_reference = client.collection(
        EXECUTION_COLLECTION
    ).document(request_id)

    transaction = client.transaction()

    @firestore.transactional
    def execute_in_transaction(
        active_transaction: firestore.Transaction,
    ) -> dict[str, Any]:
        approval_snapshot = approval_reference.get(
            transaction=active_transaction
        )

        if not approval_snapshot.exists:
            return {
                "status": "NOT_FOUND",
                "request_id": request_id,
                "message": (
                    f"Approval request {request_id} was not found."
                ),
            }

        approval_document = approval_snapshot.to_dict()

        if approval_document is None:
            return {
                "status": "INVALID_RECORD",
                "request_id": request_id,
                "message": "Approval request contains no data.",
            }

        approval_request = ApprovalRequest.model_validate(
            approval_document
        )

        execution_snapshot = execution_reference.get(
            transaction=active_transaction
        )

        if execution_snapshot.exists:
            existing_execution = execution_snapshot.to_dict()

            return {
                "status": "ALREADY_EXECUTED",
                "request_id": request_id,
                "execution": existing_execution,
                "message": (
                    "This approval request has already been executed."
                ),
            }

        if approval_request.status != ApprovalStatus.APPROVED:
            return {
                "status": "INVALID_STATE",
                "request_id": request_id,
                "current_status": approval_request.status.value,
                "message": (
                    "Only an APPROVED request can be executed."
                ),
            }

        executed_at = datetime.now(UTC)

        action_results = {
            "REVIEW_CODE_MISMATCH": (
                "Code-mismatch review case was created."
            ),
            "CORRECT_AND_RESUBMIT": (
                "Corrected claim resubmission was simulated."
            ),
            "REQUEST_CLINICAL_REVIEW": (
                "Clinical review case was created."
            ),
        }

        result_message = action_results.get(
            approval_request.action.value,
            "Approved claim-resolution action was simulated.",
        )

        execution_record = ExecutionRecord(
            execution_id=request_id,
            approval_request_id=request_id,
            claim_id=approval_request.claim_id,
            action=approval_request.action.value,
            executed_by=executed_by,
            status=ExecutionStatus.COMPLETED,
            result=result_message,
            executed_at=executed_at,
        )

        active_transaction.set(
            execution_reference,
            execution_record.model_dump(mode="python"),
        )

        active_transaction.update(
            approval_reference,
            {
                "status": ApprovalStatus.EXECUTED.value,
                "executed_at": executed_at,
            },
        )

        return {
            "status": "EXECUTED",
            "approval_request_id": request_id,
            "execution": execution_record.model_dump(mode="json"),
            "message": result_message,
        }

    return execute_in_transaction(transaction)


def find_execution(
    approval_request_id: str,
) -> ExecutionRecord | None:
    """Retrieve an execution record by approval request ID."""
    normalized_id = approval_request_id.strip()

    if not normalized_id:
        return None

    client = get_firestore_client()

    snapshot = client.collection(
        EXECUTION_COLLECTION
    ).document(normalized_id).get()

    if not snapshot.exists:
        return None

    document = snapshot.to_dict()

    if document is None:
        return None

    return ExecutionRecord.model_validate(document)