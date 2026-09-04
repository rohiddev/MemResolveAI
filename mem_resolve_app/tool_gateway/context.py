from contextvars import ContextVar
from dataclasses import dataclass, field
from uuid import uuid4


@dataclass(frozen=True)
class ToolRequestContext:
    correlation_id: str
    user_id: str
    agent_name: str
    roles: tuple[str, ...] = field(default_factory=tuple)


_current_context: ContextVar[ToolRequestContext | None] = ContextVar(
    "memresolve_tool_context",
    default=None,
)


LOCAL_AGENT_ROLES: dict[str, tuple[str, ...]] = {
    "claim_agent": ("provider_ops",),
    "authorization_agent": ("provider_ops",),
    "eligibility_agent": ("provider_ops",),
    "policy_agent": ("provider_ops",),
    "approval_agent": ("provider_ops",),
    "reviewer_agent": ("claim_reviewer",),
    "executor_agent": ("action_executor",),
}


def create_local_context(
    agent_name: str,
    user_id: str = "local-development-user",
    roles: tuple[str, ...] | None = None,
) -> ToolRequestContext:
    """Create a request context for local ADK development."""
    resolved_roles = roles

    if resolved_roles is None:
        resolved_roles = LOCAL_AGENT_ROLES.get(
            agent_name,
            ("provider_ops",),
        )

    return ToolRequestContext(
        correlation_id=str(uuid4()),
        user_id=user_id,
        agent_name=agent_name,
        roles=resolved_roles,
    )


def set_tool_context(
    context: ToolRequestContext,
) -> None:
    """Set the authenticated context for the current request."""
    _current_context.set(context)


def clear_tool_context() -> None:
    """Clear the current request context."""
    _current_context.set(None)


def get_tool_context(
    agent_name: str,
) -> ToolRequestContext:
    """Return the current context or create a local fallback.

    When an authenticated request context exists, its user identity,
    roles, and correlation ID are retained while the active specialist
    agent name is applied.
    """
    existing_context = _current_context.get()

    if existing_context is not None:
        return ToolRequestContext(
            correlation_id=existing_context.correlation_id,
            user_id=existing_context.user_id,
            agent_name=agent_name,
            roles=existing_context.roles,
        )

    return create_local_context(
        agent_name=agent_name,
    )