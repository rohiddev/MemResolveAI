from functools import lru_cache

from mem_resolve_app.config import get_settings
from mem_resolve_app.knowledge.base import PolicyRetriever


@lru_cache
def get_policy_retriever() -> PolicyRetriever:
    """Create and cache the configured policy retrieval backend.

    Returns:
        ChromaPolicyRetriever for local development or
        VertexPolicyRetriever for GCP.

    Raises:
        ValueError: When KNOWLEDGE_BACKEND contains an unsupported value.
    """
    settings = get_settings()
    backend = settings.knowledge_backend.strip().lower()

    if backend == "chroma":
        # Delayed import keeps Chroma out of the GCP deployment path
        # when Vertex AI RAG is selected.
        from mem_resolve_app.knowledge.chroma_retriever import (
            ChromaPolicyRetriever,
        )

        return ChromaPolicyRetriever()

    if backend == "vertex":
        # This implementation will be added when we configure
        # Vertex AI RAG for the GCP deployment.
        from mem_resolve_app.knowledge.vertex_retriever import (
            VertexPolicyRetriever,
        )

        return VertexPolicyRetriever()

    raise ValueError(
        "Unsupported knowledge backend "
        f"{settings.knowledge_backend!r}. "
        "Allowed values are 'chroma' and 'vertex'."
    )