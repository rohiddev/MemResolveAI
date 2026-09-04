from types import SimpleNamespace
from typing import Any

from mem_resolve_app.models.approval import ApprovalStatus
from mem_resolve_app.repositories import execution_repository


class FakeSnapshot:
    def __init__(self, document: dict[str, Any] | None):
        self._document = document

    @property
    def exists(self) -> bool:
        return self._document is not None

    def to_dict(self) -> dict[str, Any] | None:
        if self._document is None:
            return None

        return dict(self._document)


class FakeDocumentReference:
    def __init__(
        self,
        store: dict[str, dict[str, dict[str, Any]]],
        collection_name: str,
        document_id: str,
    ):
        self.store = store
        self.collection_name = collection_name
        self.document_id = document_id

    def get(self, transaction: Any = None) -> FakeSnapshot:
        del transaction

        collection = self.store.setdefault(
            self.collection_name,
            {},
        )
        return FakeSnapshot(collection.get(self.document_id))


class FakeCollectionReference:
    def __init__(
        self,
        store: dict[str, dict[str, dict[str, Any]]],
        collection_name: str,
    ):
        self.store = store
        self.collection_name = collection_name

    def document(self, document_id: str) -> FakeDocumentReference:
        return FakeDocumentReference(
            store=self.store,
            collection_name=self.collection_name,
            document_id=document_id,
        )


class FakeTransaction:
    def __init__(
        self,
        store: dict[str, dict[str, dict[str, Any]]],
    ):
        self.store = store

    def set(
        self,
        reference: FakeDocumentReference,
        document: dict[str, Any],
    ) -> None:
        collection = self.store.setdefault(
            reference.collection_name,
            {},
        )
        collection[reference.document_id] = dict(document)

    def update(
        self,
        reference: FakeDocumentReference,
        changes: dict[str, Any],
    ) -> None:
        collection = self.store.setdefault(
            reference.collection_name,
            {},
        )
        collection[reference.document_id].update(changes)


class FakeFirestoreClient:
    def __init__(
        self,
        store: dict[str, dict[str, dict[str, Any]]],
    ):
        self.store = store

    def collection(
        self,
        collection_name: str,
    ) -> FakeCollectionReference:
        return FakeCollectionReference(
            store=self.store,
            collection_name=collection_name,
        )

    def transaction(self) -> FakeTransaction:
        return FakeTransaction(self.store)


def test_approved_action_executes_exactly_once(
    monkeypatch,
) -> None:
    request_id = "approval-test-001"

    store: dict[str, dict[str, dict[str, Any]]] = {
        execution_repository.APPROVAL_COLLECTION: {
            request_id: {
                "request_id": request_id,
                "status": "APPROVED",
            }
        },
        execution_repository.EXECUTION_COLLECTION: {},
    }

    fake_client = FakeFirestoreClient(store)

    fake_approval = SimpleNamespace(
        status=ApprovalStatus.APPROVED,
        action=SimpleNamespace(value="REVIEW_CODE_MISMATCH"),
        claim_id="CLM-20045",
    )

    monkeypatch.setattr(
        execution_repository,
        "get_firestore_client",
        lambda: fake_client,
    )

    monkeypatch.setattr(
        execution_repository.firestore,
        "transactional",
        lambda function: function,
    )

    monkeypatch.setattr(
        execution_repository.ApprovalRequest,
        "model_validate",
        staticmethod(lambda document: fake_approval),
    )

    first_result = execution_repository.execute_approval_once(
        request_id=request_id,
        executed_by="executor-01",
    )

    second_result = execution_repository.execute_approval_once(
        request_id=request_id,
        executed_by="executor-02",
    )

    assert first_result["status"] == "EXECUTED"
    assert first_result["execution"]["claim_id"] == "CLM-20045"
    assert first_result["execution"]["executed_by"] == "executor-01"
    assert (
        first_result["execution"]["action"]
        == "REVIEW_CODE_MISMATCH"
    )

    assert second_result["status"] == "ALREADY_EXECUTED"
    assert (
        second_result["execution"]["executed_by"]
        == "executor-01"
    )

    execution_documents = store[
        execution_repository.EXECUTION_COLLECTION
    ]
    assert len(execution_documents) == 1

    approval_document = store[
        execution_repository.APPROVAL_COLLECTION
    ][request_id]
    assert approval_document["status"] == "EXECUTED"

def test_non_approved_requests_are_not_executed(
    monkeypatch,
) -> None:
    for approval_status in (
        ApprovalStatus.PENDING_APPROVAL,
        ApprovalStatus.REJECTED,
    ):
        request_id = f"approval-{approval_status.value.lower()}"

        store: dict[str, dict[str, dict[str, Any]]] = {
            execution_repository.APPROVAL_COLLECTION: {
                request_id: {
                    "request_id": request_id,
                    "status": approval_status.value,
                }
            },
            execution_repository.EXECUTION_COLLECTION: {},
        }

        fake_client = FakeFirestoreClient(store)

        fake_approval = SimpleNamespace(
            status=approval_status,
            action=SimpleNamespace(
                value="REVIEW_CODE_MISMATCH"
            ),
            claim_id="CLM-20045",
        )

        monkeypatch.setattr(
            execution_repository,
            "get_firestore_client",
            lambda: fake_client,
        )

        monkeypatch.setattr(
            execution_repository.firestore,
            "transactional",
            lambda function: function,
        )

        monkeypatch.setattr(
            execution_repository.ApprovalRequest,
            "model_validate",
            staticmethod(lambda document: fake_approval),
        )

        result = execution_repository.execute_approval_once(
            request_id=request_id,
            executed_by="executor-01",
        )

        assert result["status"] == "INVALID_STATE"
        assert result["current_status"] == approval_status.value
        assert (
            result["message"]
            == "Only an APPROVED request can be executed."
        )

        execution_documents = store[
            execution_repository.EXECUTION_COLLECTION
        ]
        assert execution_documents == {}

        approval_document = store[
            execution_repository.APPROVAL_COLLECTION
        ][request_id]
        assert approval_document["status"] == approval_status.value