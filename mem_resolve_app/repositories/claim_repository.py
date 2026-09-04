from mem_resolve_app.models.claim import Claim
from mem_resolve_app.repositories.firestore_client import (
    get_firestore_client,
)


COLLECTION_NAME = "memresolve_claims"


def find_claim(claim_id: str) -> Claim | None:
    """Retrieve a claim from Firestore using its claim ID.

    Args:
        claim_id: Claim identifier such as CLM-20045.

    Returns:
        A validated Claim object, or None when the claim does not exist.
    """
    normalized_claim_id = claim_id.strip().upper()

    if not normalized_claim_id:
        return None

    client = get_firestore_client()

    document_reference = client.collection(
        COLLECTION_NAME
    ).document(normalized_claim_id)

    snapshot = document_reference.get()

    if not snapshot.exists:
        return None

    document = snapshot.to_dict()

    if document is None:
        return None

    return Claim.model_validate(document)