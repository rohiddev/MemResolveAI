from datetime import UTC, datetime
from typing import Any

from mem_resolve_app.repositories.firestore_client import (
    get_firestore_client,
)


CLAIMS: dict[str, dict[str, Any]] = {
    "CLM-20045": {
        "claim_id": "CLM-20045",
        "member_id": "MBR-1001",
        "provider_id": "PRV-501",
        "service_date": "2026-07-15",
        "procedure_code": "72148",
        "diagnosis_code": "M54.50",
        "billed_amount": "1400.00",
        "allowed_amount": "0.00",
        "status": "DENIED",
        "denial_code": "AUTH_CODE_MISMATCH",
        "denial_reason": (
            "The billed procedure code does not match the procedure "
            "code on the authorization."
        ),
        "authorization_id": "AUTH-9001",
    },
    "CLM-20046": {
        "claim_id": "CLM-20046",
        "member_id": "MBR-1002",
        "provider_id": "PRV-502",
        "service_date": "2026-07-18",
        "procedure_code": "99214",
        "diagnosis_code": "I10",
        "billed_amount": "225.00",
        "allowed_amount": "175.00",
        "status": "PAID",
        "denial_code": None,
        "denial_reason": None,
        "authorization_id": None,
    },
}


ELIGIBILITY_RECORDS: dict[str, dict[str, Any]] = {
    "MBR-1001": {
        "member_id": "MBR-1001",
        "plan_name": "Choice Plus Gold",
        "plan_type": "PPO",
        "group_number": "GRP-100",
        "effective_date": "2026-01-01",
        "termination_date": None,
        "status": "ACTIVE",
    },
    "MBR-1002": {
        "member_id": "MBR-1002",
        "plan_name": "Navigate Silver",
        "plan_type": "HMO",
        "group_number": "GRP-200",
        "effective_date": "2026-01-01",
        "termination_date": "2026-12-31",
        "status": "ACTIVE",
    },
    "MBR-1003": {
        "member_id": "MBR-1003",
        "plan_name": "Choice Plus Bronze",
        "plan_type": "PPO",
        "group_number": "GRP-300",
        "effective_date": "2025-01-01",
        "termination_date": "2026-06-30",
        "status": "INACTIVE",
    },
}


AUTHORIZATIONS: dict[str, dict[str, Any]] = {
    "AUTH-9001": {
        "authorization_id": "AUTH-9001",
        "member_id": "MBR-1001",
        "provider_id": "PRV-501",
        "procedure_code": "72141",
        "diagnosis_code": "M54.50",
        "approved_from": "2026-07-01",
        "approved_through": "2026-07-31",
        "approved_units": 1,
        "status": "APPROVED",
    },
    "AUTH-9002": {
        "authorization_id": "AUTH-9002",
        "member_id": "MBR-1003",
        "provider_id": "PRV-503",
        "procedure_code": "70551",
        "diagnosis_code": "R51.9",
        "approved_from": "2026-08-01",
        "approved_through": "2026-08-31",
        "approved_units": 1,
        "status": "PENDING",
    },
}


def seed_collection(
    collection_name: str,
    documents: dict[str, dict[str, Any]],
) -> int:
    """Write synthetic documents into a Firestore collection."""
    client = get_firestore_client()
    batch = client.batch()
    seeded_at = datetime.now(UTC)

    for document_id, document in documents.items():
        reference = client.collection(collection_name).document(document_id)

        stored_document = {
            **document,
            "synthetic": True,
            "seeded_at": seeded_at,
        }

        batch.set(
            reference,
            stored_document,
            merge=True,
        )

    batch.commit()
    return len(documents)


def main() -> None:
    """Seed all MemResolveAI operational collections."""
    client = get_firestore_client()

    print(f"Firestore project: {client.project}")
    print(f"Firestore database: {client._database}")

    claim_count = seed_collection(
        collection_name="memresolve_claims",
        documents=CLAIMS,
    )

    eligibility_count = seed_collection(
        collection_name="memresolve_eligibility",
        documents=ELIGIBILITY_RECORDS,
    )

    authorization_count = seed_collection(
        collection_name="memresolve_authorizations",
        documents=AUTHORIZATIONS,
    )

    print(f"Seeded claims: {claim_count}")
    print(f"Seeded eligibility records: {eligibility_count}")
    print(f"Seeded authorizations: {authorization_count}")
    print("Firestore seeding completed.")


if __name__ == "__main__":
    main()