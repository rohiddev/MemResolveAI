from uuid import UUID

import pytest

from mem_resolve_app.tool_gateway.context import (
    ToolRequestContext,
    clear_tool_context,
    get_tool_context,
    set_tool_context,
)


@pytest.fixture(autouse=True)
def reset_tool_context() -> None:
    clear_tool_context()
    yield
    clear_tool_context()


def test_authenticated_identity_and_correlation_are_preserved() -> None:
    original_context = ToolRequestContext(
        correlation_id="correlation-authenticated-001",
        user_id="authenticated-user-001",
        agent_name="resolution_supervisor",
        roles=("claim_reviewer",),
    )

    set_tool_context(original_context)

    specialist_context = get_tool_context(
        agent_name="policy_agent",
    )

    assert (
        specialist_context.correlation_id
        == "correlation-authenticated-001"
    )
    assert (
        specialist_context.user_id
        == "authenticated-user-001"
    )
    assert specialist_context.agent_name == "policy_agent"
    assert specialist_context.roles == ("claim_reviewer",)


def test_local_executor_receives_only_executor_role() -> None:
    executor_context = get_tool_context(
        agent_name="executor_agent",
    )

    assert executor_context.agent_name == "executor_agent"
    assert executor_context.user_id == "local-development-user"
    assert executor_context.roles == ("action_executor",)

    # The generated correlation ID must be a valid UUID.
    UUID(executor_context.correlation_id)


def test_clearing_context_removes_authenticated_identity() -> None:
    set_tool_context(
        ToolRequestContext(
            correlation_id="correlation-authenticated-002",
            user_id="authenticated-user-002",
            agent_name="resolution_supervisor",
            roles=("claim_reviewer",),
        )
    )

    clear_tool_context()

    local_context = get_tool_context(
        agent_name="claim_agent",
    )

    assert local_context.user_id == "local-development-user"
    assert local_context.roles == ("provider_ops",)
    assert (
        local_context.correlation_id
        != "correlation-authenticated-002"
    )