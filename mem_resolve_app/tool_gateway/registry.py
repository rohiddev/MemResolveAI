from dataclasses import dataclass
from enum import StrEnum


class ToolRisk(StrEnum):
    """Risk classification for agent-accessible tools."""

    READ = "READ"
    APPROVAL = "APPROVAL"
    WRITE = "WRITE"


@dataclass(frozen=True)
class ToolRegistration:
    """Governance rules associated with one tool."""

    name: str
    risk: ToolRisk
    allowed_agents: tuple[str, ...]
    allowed_roles: tuple[str, ...]
    requires_approval: bool = False


TOOL_REGISTRY: dict[str, ToolRegistration] = {
    "get_claim": ToolRegistration(
        name="get_claim",
        risk=ToolRisk.READ,
        allowed_agents=(
            "claim_agent",
        ),
        allowed_roles=(
            "provider_ops",
            "claim_reviewer",
            "action_executor",
        ),
    ),
    "get_authorization": ToolRegistration(
        name="get_authorization",
        risk=ToolRisk.READ,
        allowed_agents=(
            "authorization_agent",
        ),
        allowed_roles=(
            "provider_ops",
            "claim_reviewer",
            "action_executor",
        ),
    ),
    "check_eligibility": ToolRegistration(
        name="check_eligibility",
        risk=ToolRisk.READ,
        allowed_agents=(
            "eligibility_agent",
        ),
        allowed_roles=(
            "provider_ops",
            "claim_reviewer",
        ),
    ),
    "search_claim_policy": ToolRegistration(
        name="search_claim_policy",
        risk=ToolRisk.READ,
        allowed_agents=(
            "policy_agent",
        ),
        allowed_roles=(
            "provider_ops",
            "claim_reviewer",
        ),
    ),
    "create_approval_request": ToolRegistration(
        name="create_approval_request",
        risk=ToolRisk.APPROVAL,
        allowed_agents=(
            "approval_agent",
        ),
        allowed_roles=(
            "provider_ops",
            "claim_reviewer",
        ),
    ),
    "get_approval_request": ToolRegistration(
        name="get_approval_request",
        risk=ToolRisk.READ,
        allowed_agents=(
            "approval_agent",
            "reviewer_agent",
            "executor_agent",
        ),
        allowed_roles=(
            "provider_ops",
            "claim_reviewer",
            "action_executor",
        ),
    ),
    "approve_request": ToolRegistration(
        name="approve_request",
        risk=ToolRisk.APPROVAL,
        allowed_agents=(
            "reviewer_agent",
        ),
        allowed_roles=(
            "claim_reviewer",
        ),
    ),
    "reject_request": ToolRegistration(
        name="reject_request",
        risk=ToolRisk.APPROVAL,
        allowed_agents=(
            "reviewer_agent",
        ),
        allowed_roles=(
            "claim_reviewer",
        ),
    ),
    "execute_approved_action": ToolRegistration(
        name="execute_approved_action",
        risk=ToolRisk.WRITE,
        allowed_agents=(
            "executor_agent",
        ),
        allowed_roles=(
            "action_executor",
        ),
        requires_approval=True,
    ),
    "get_execution": ToolRegistration(
        name="get_execution",
        risk=ToolRisk.READ,
        allowed_agents=(
            "executor_agent",
        ),
        allowed_roles=(
            "action_executor",
            "claim_reviewer",
        ),
    ),
}


def get_tool_registration(
    tool_name: str,
) -> ToolRegistration | None:
    """Return the governance registration for a tool.

    Args:
        tool_name: Registered agent-facing tool name.

    Returns:
        Tool registration or None when the tool is not registered.
    """
    return TOOL_REGISTRY.get(tool_name)