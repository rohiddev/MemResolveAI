from google.cloud.firestore_v1.base_query import FieldFilter

from mem_resolve_app.models.approval import (
    ApprovalRequest,
    ApprovalStatus,
    ClaimAction,
)
from mem_resolve_app.repositories.firestore_client import (
    get_firestore_client,
)


COLLECTION_NAME = "memresolve_approval_requests"


def save_approval_request(
    request: ApprovalRequest,
) -> ApprovalRequest:
    """Create or update an approval request in Firestore.

    Args:
        request: Validated approval request.

    Returns:
        The saved approval request.
    """
    client = get_firestore_client()

    document_reference = client.collection(
        COLLECTION_NAME
    ).document(request.request_id)

    document_reference.set(
        request.model_dump(mode="python"),
        merge=True,
    )

    return request


def find_approval_request(
    request_id: str,
) -> ApprovalRequest | None:
    """Retrieve an approval request from Firestore by request ID.

    Args:
        request_id: Unique approval request identifier.

    Returns:
        A validated approval request, or None when it is not found.
    """
    normalized_request_id = request_id.strip()

    if not normalized_request_id:
        return None

    client = get_firestore_client()

    document_reference = client.collection(
        COLLECTION_NAME
    ).document(normalized_request_id)

    snapshot = document_reference.get()

    if not snapshot.exists:
        return None

    document = snapshot.to_dict()

    if document is None:
        return None

    return ApprovalRequest.model_validate(document)


def find_pending_request(
    claim_id: str,
    action: ClaimAction,
) -> ApprovalRequest | None:
    """Find an existing pending request for a claim and action.

    This prevents duplicate pending approval requests.

    Args:
        claim_id: Claim identifier such as CLM-20045.
        action: Proposed controlled claim action.

    Returns:
        An existing pending request, or None.
    """
    normalized_claim_id = claim_id.strip().upper()
    client = get_firestore_client()

    query = (
        client.collection(COLLECTION_NAME)
        .where(
            filter=FieldFilter(
                "claim_id",
                "==",
                normalized_claim_id,
            )
        )
    )

    for snapshot in query.stream():
        document = snapshot.to_dict()

        if document is None:
            continue

        request = ApprovalRequest.model_validate(document)

        if (
            request.action == action
            and request.status == ApprovalStatus.PENDING_APPROVAL
        ):
            return request

    return None


def list_approval_requests() -> list[ApprovalRequest]:
    """Return all approval requests from Firestore.

    Returns:
        Validated approval requests ordered by creation time.
    """
    client = get_firestore_client()
    requests: list[ApprovalRequest] = []

    for snapshot in client.collection(COLLECTION_NAME).stream():
        document = snapshot.to_dict()

        if document is None:
            continue

        requests.append(
            ApprovalRequest.model_validate(document)
        )

    requests.sort(
        key=lambda request: request.created_at,
        reverse=True,
    )

    return requests