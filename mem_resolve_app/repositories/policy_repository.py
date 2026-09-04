from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
POLICY_DIRECTORY = PROJECT_ROOT / "data" / "policies"


def load_policy_documents() -> list[dict[str, str]]:
    """Load local Markdown policy documents."""
    documents: list[dict[str, str]] = []

    if not POLICY_DIRECTORY.exists():
        return documents

    for file_path in sorted(POLICY_DIRECTORY.glob("*.md")):
        documents.append(
            {
                "source": file_path.name,
                "content": file_path.read_text(encoding="utf-8"),
            }
        )

    return documents