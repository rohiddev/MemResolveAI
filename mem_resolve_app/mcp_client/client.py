import asyncio
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from mcp import Client, StdioServerParameters


def get_local_server_parameters() -> StdioServerParameters:
    """Describe how to launch the local MemResolveAI MCP server.

    The MCP subprocess uses the same Python interpreter and inherits
    the parent application's configuration and credentials.
    """
    return StdioServerParameters(
        command=sys.executable,
        args=[
            "-m",
            "mem_resolve_mcp.server",
        ],
        env=os.environ.copy(),
    )


def _extract_tool_result(
    result: Any,
) -> dict[str, Any]:
    """Convert an MCP CallToolResult into a regular dictionary.

    MCP tools can return structured content or text content. This
    function handles both response formats.
    """
    structured_content = getattr(
        result,
        "structured_content",
        None,
    )

    if isinstance(structured_content, dict):
        return structured_content

    if structured_content is not None:
        return {
            "status": "STRUCTURED_RESPONSE",
            "content": structured_content,
        }

    content_blocks = getattr(
        result,
        "content",
        [],
    )

    text_values: list[str] = []

    for block in content_blocks:
        text_value = getattr(
            block,
            "text",
            None,
        )

        if text_value is not None:
            text_values.append(text_value)

    combined_text = "\n".join(text_values)

    if not combined_text:
        return {
            "status": "EMPTY_RESPONSE",
            "message": "The MCP tool returned no content.",
        }

    try:
        parsed_content = json.loads(combined_text)
    except json.JSONDecodeError:
        return {
            "status": "TEXT_RESPONSE",
            "content": combined_text,
        }

    if isinstance(parsed_content, dict):
        return parsed_content

    return {
        "status": "STRUCTURED_RESPONSE",
        "content": parsed_content,
    }


async def list_local_mcp_tools() -> list[str]:
    """Start the local MCP server and return its tool names.

    The MCP server subprocess is started when the asynchronous
    context is entered and stopped when the context is exited.
    """
    server_parameters = get_local_server_parameters()

    async with Client(server_parameters) as client:
        response = await client.list_tools()

        return [
            tool.name
            for tool in response.tools
        ]


async def call_local_mcp_tool(
    tool_name: str,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Call a tool on the local MemResolveAI MCP server.

    Args:
        tool_name: Registered MCP tool name.
        arguments: Arguments passed to the MCP tool.

    Returns:
        A dictionary containing the MCP tool result.
    """
    server_parameters = get_local_server_parameters()

    async with Client(server_parameters) as client:
        result = await client.call_tool(
            tool_name,
            arguments,
        )

        extracted_result = _extract_tool_result(result)

        if getattr(result, "is_error", False):
            return {
                "status": "MCP_ERROR",
                "tool_name": tool_name,
                "result": extracted_result,
            }

        return extracted_result


def call_local_mcp_tool_sync(
    tool_name: str,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """Call an asynchronous MCP tool from synchronous agent code.

    When no event loop is running, asyncio.run executes the call
    directly.

    When an event loop is already running, the call is executed in
    a separate thread with its own event loop.

    Args:
        tool_name: Registered MCP tool name.
        arguments: Arguments passed to the MCP tool.

    Returns:
        A dictionary containing the MCP tool result.
    """

    async def invoke() -> dict[str, Any]:
        return await call_local_mcp_tool(
            tool_name=tool_name,
            arguments=arguments,
        )

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(invoke())

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(
            lambda: asyncio.run(invoke())
        )

        return future.result()