from typing import Any, Protocol


class PolicyRetriever(Protocol):
    """Common interface implemented by policy retrieval backends.

    Both the local Chroma retriever and the GCP Vertex AI retriever
    must implement this search method.
    """

    def search(
        self,
        *,
        query: str,
        maximum_results: int = 3,
    ) -> list[dict[str, Any]]:
        """Retrieve policy sections relevant to a query.

        Args:
            query: Natural-language policy question.
            maximum_results: Maximum number of matching sections.

        Returns:
            Policy matches with content and source metadata.
        """
        ...