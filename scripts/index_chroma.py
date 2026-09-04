import re
from pathlib import Path

from mem_resolve_app.knowledge.chroma_retriever import (
    ChromaPolicyRetriever,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
POLICY_DIRECTORY = PROJECT_ROOT / "data" / "policies"


def split_markdown_sections(
    *,
    source: str,
    content: str,
) -> list[dict[str, str]]:
    """Split a Markdown policy into independently retrievable sections."""
    sections: list[dict[str, str]] = []
    current_heading = "Document"
    current_lines: list[str] = []

    def save_current_section() -> None:
        body = "\n".join(current_lines).strip()

        if not body:
            return

        sections.append(
            {
                "source": source,
                "heading": current_heading,
                "content": f"# {current_heading}\n\n{body}",
            }
        )

    for line in content.splitlines():
        heading_match = re.match(r"^#{1,3}\s+(.+)$", line)

        if heading_match:
            save_current_section()
            current_lines.clear()
            current_heading = heading_match.group(1).strip()
            continue

        current_lines.append(line)

    save_current_section()
    return sections


def load_policy_sections() -> list[dict[str, str]]:
    """Load and split every Markdown policy file."""
    sections: list[dict[str, str]] = []

    for file_path in sorted(POLICY_DIRECTORY.glob("*.md")):
        content = file_path.read_text(encoding="utf-8")

        sections.extend(
            split_markdown_sections(
                source=file_path.name,
                content=content,
            )
        )

    return sections


def create_document_id(
    *,
    source: str,
    heading: str,
    position: int,
) -> str:
    """Create a stable Chroma document ID."""
    normalized_source = re.sub(
        r"[^a-zA-Z0-9]+",
        "-",
        source,
    ).strip("-").lower()

    normalized_heading = re.sub(
        r"[^a-zA-Z0-9]+",
        "-",
        heading,
    ).strip("-").lower()

    return f"{normalized_source}-{position}-{normalized_heading}"


def main() -> None:
    """Index local policy sections into Chroma."""
    sections = load_policy_sections()

    if not sections:
        print(f"No policy documents found in {POLICY_DIRECTORY}")
        return

    document_ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict[str, str | int]] = []

    for position, section in enumerate(sections, start=1):
        document_ids.append(
            create_document_id(
                source=section["source"],
                heading=section["heading"],
                position=position,
            )
        )

        documents.append(section["content"])

        metadatas.append(
            {
                "source": section["source"],
                "heading": section["heading"],
                "position": position,
            }
        )

    retriever = ChromaPolicyRetriever()

    indexed_count = retriever.upsert_documents(
        ids=document_ids,
        documents=documents,
        metadatas=metadatas,
    )

    print(f"Policy directory: {POLICY_DIRECTORY}")
    print(f"Indexed policy sections: {indexed_count}")
    print(f"Chroma collection count: {retriever.count()}")


if __name__ == "__main__":
    main()