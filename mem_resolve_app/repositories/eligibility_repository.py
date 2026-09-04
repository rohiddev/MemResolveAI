from datetime import date

from mem_resolve_app.models.eligibility import (
    CoverageStatus,
    EligibilityRecord,
)
from mem_resolve_app.repositories.firestore_client import (
    get_firestore_client,
)


COLLECTION_NAME = "memresolve_eligibility"


def find_eligibility(
    member_id: str,
) -> EligibilityRecord | None:
    """Retrieve a member's eligibility record from Firestore.

    Args:
        member_id: Member identifier such as MBR-1001.

    Returns:
        A validated eligibility record, or None when it is not found.
    """
    normalized_member_id = member_id.strip().upper()

    if not normalized_member_id:
        return None

    client = get_firestore_client()

    document_reference = client.collection(
        COLLECTION_NAME
    ).document(normalized_member_id)

    snapshot = document_reference.get()

    if not snapshot.exists:
        return None

    document = snapshot.to_dict()

    if document is None:
        return None

    return EligibilityRecord.model_validate(document)


def is_covered_on_date(
    record: EligibilityRecord,
    service_date: date,
) -> bool:
    """Determine whether coverage applies on a service date.

    The determination is performed by deterministic Python logic,
    not by the LLM.
    """
    if record.status != CoverageStatus.ACTIVE:
        return False

    if service_date < record.effective_date:
        return False

    if (
        record.termination_date is not None
        and service_date > record.termination_date
    ):
        return False

    return True