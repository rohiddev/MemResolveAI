import asyncio
import json

from mem_resolve_app.agent import root_agent
from mem_resolve_app.config import get_settings
from mem_resolve_app.knowledge.factory import get_policy_retriever
from mem_resolve_app.mcp_client.client import list_local_mcp_tools


EXPECTED_MCP_TOOLS = {
    "get_claim",
    "get_authorization",
    "check_eligibility",
    "create_approval_request",
    "get_approval_request",
    "approve_request",
    "reject_request",
    "execute_approved_action",
    "get_execution",
}


async def verify_readiness() -> None:
    settings = get_settings()

    mcp_tools = set(await list_local_mcp_tools())
    missing_mcp_tools = EXPECTED_MCP_TOOLS - mcp_tools
    unexpected_mcp_tools = mcp_tools - EXPECTED_MCP_TOOLS

    policy_retriever = get_policy_retriever()
    policy_document_count = policy_retriever.count()

    checks = {
        "configuration_loaded": True,
        "root_agent_loaded": root_agent is not None,
        "root_agent_name": root_agent.name,
        "google_cloud_project": settings.google_cloud_project,
        "google_cloud_location": settings.google_cloud_location,
        "model": settings.mem_resolve_model,
        "data_backend": settings.data_backend,
        "knowledge_backend": settings.knowledge_backend,
        "mcp_transport": settings.mcp_transport,
        "mcp_tools": sorted(mcp_tools),
        "missing_mcp_tools": sorted(missing_mcp_tools),
        "unexpected_mcp_tools": sorted(unexpected_mcp_tools),
        "policy_document_count": policy_document_count,
    }

    print(json.dumps(checks, indent=2))

    failures: list[str] = []

    if root_agent is None:
        failures.append("Root agent could not be loaded.")

    if root_agent.name != "resolution_supervisor":
        failures.append(
            "Root agent name must be resolution_supervisor."
        )

    if missing_mcp_tools:
        failures.append(
            "Required MCP tools are missing: "
            + ", ".join(sorted(missing_mcp_tools))
        )

    if policy_document_count < 1:
        failures.append(
            "The policy knowledge collection is empty."
        )

    if failures:
        print("\nReadiness verification failed:")

        for failure in failures:
            print(f"- {failure}")

        raise SystemExit(1)

    print("\nMemResolve AI readiness verification passed.")


def main() -> None:
    asyncio.run(verify_readiness())


if __name__ == "__main__":
    main()