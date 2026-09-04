import os
import sys

from mem_resolve_app.mcp_client.client import (
    get_local_server_parameters,
)


def test_mcp_subprocess_inherits_parent_environment(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "GOOGLE_CLOUD_PROJECT",
        "memresolve-test-project",
    )
    monkeypatch.setenv(
        "GOOGLE_APPLICATION_CREDENTIALS",
        "/tmp/test-adc.json",
    )

    parameters = get_local_server_parameters()

    assert parameters.command == sys.executable
    assert parameters.args == [
        "-m",
        "mem_resolve_mcp.server",
    ]
    assert parameters.env is not None
    assert (
        parameters.env["GOOGLE_CLOUD_PROJECT"]
        == "memresolve-test-project"
    )
    assert (
        parameters.env["GOOGLE_APPLICATION_CREDENTIALS"]
        == "/tmp/test-adc.json"
    )

    # Ensure the environment passed to the child is a copy.
    assert parameters.env is not os.environ