from typing import Any

from mem_resolve_app.config import get_settings


class ChromaPolicyRetriever:
    """Stores and retrieves policy sections using local Chroma."""

    def __init__(self) -> None:
        # Import Chroma only when the Chroma backend is selected.
        # This keeps Chroma out of the GCP Agent Runtime path.
        import chromadb

        settings = get_settings()

        self._client = chromadb.PersistentClient(
            path=str(settings.chroma_directory),
        )

        self._collection = self._client.get_or_create_collection(
            name=settings.chroma_collection,
            metadata={
                "application": "MemResolveAI",
                "content_type": "policy",
            },
        )

    def upsert_documents(
        self,
        *,
        ids: list[str],
        documents: list[str],
        metadatas: list[dict[str, Any]],
    ) -> int:
        """Insert or update policy sections in Chroma."""
        if not ids:
            return 0

        self._collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )

        return len(ids)

    def search(
        self,
        *,
        query: str,
        maximum_results: int = 3,
    ) -> list[dict[str, Any]]:
        """Return policy sections relevant to a query."""
        normalized_query = query.strip()

        if not normalized_query:
            return []

        collection_count = self._collection.count()

        if collection_count == 0:
            return []

        result_count = min(maximum_results, collection_count)

        query_result = self._collection.query(
            query_texts=[normalized_query],
            n_results=result_count,
            include=[
                "documents",
                "metadatas",
                "distances",
            ],
        )

        documents = query_result.get("documents") or [[]]
        metadatas = query_result.get("metadatas") or [[]]
        distances = query_result.get("distances") or [[]]
        ids = query_result.get("ids") or [[]]

        matches: list[dict[str, Any]] = []

        for document_id, document, metadata, distance in zip(
            ids[0],
            documents[0],
            metadatas[0],
            distances[0],
            strict=True,
        ):
            matches.append(
                {
                    "document_id": document_id,
                    "content": document,
                    "metadata": metadata or {},
                    "distance": round(float(distance), 6),
                }
            )

        return matches

    def count(self) -> int:
        """Return the number of indexed policy sections."""
        return self._collection.count()