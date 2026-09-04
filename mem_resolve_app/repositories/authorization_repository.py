from mem_resolve_app.models.authorization import Authorization
from mem_resolve_app.repositories.firestore_client import (
    get_firestore_client,
)


COLLECTION_NAME = "memresolve_authorizations"


def find_authorization(
    authorization_id: str,
) -> Authorization | None:
    """Retrieve an authorization from Firestore.

    Args:
        authorization_id: Authorization identifier such as AUTH-9001.

    Returns:
        A validated Authorization object, or None when it is not found.
    """
    normalized_authorization_id = authorization_id.strip().upper()

    if not normalized_authorization_id:
        return None

    client = get_firestore_client()

    document_reference = client.collection(
        COLLECTION_NAME
    ).document(normalized_authorization_id)

    snapshot = document_reference.get()

    if not snapshot.exists:
        return None

    document = snapshot.to_dict()

    if document is None:
        return None

    return Authorization.model_validate(document)