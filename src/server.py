# Copyright (c) 2025 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""MCP Server setup for the Marketplace Crawler."""

from dedalus_mcp import MCPServer, tool
from dedalus_mcp.server import TransportSecuritySettings

from crawler import ScanResult, scan_marketplace_sync


@tool(
    description="Scan the Dedalus Marketplace and list all available MCP servers with their details including names, descriptions, GitHub URLs, and optionally tools."
)
async def scan_marketplace(include_tools: bool = False) -> ScanResult:
    """
    Scan the Dedalus Marketplace to discover all available MCP servers.

    This tool fetches the list of all servers from the Dedalus Marketplace,
    extracting their names, descriptions, GitHub repository URLs, and metadata.

    Args:
        include_tools: If True, also fetch tool information for each server.
                      This requires visiting each server's detail page and
                      will be slower but provides complete information.
                      Defaults to False for faster results.

    Returns:
        ScanResult containing:
        - total_servers: Number of servers found
        - servers: List of ServerInfo objects with:
          - name: Server name
          - slug: Full slug (publisher/name)
          - publisher: Publisher/organization name
          - description: Server description
          - github_url: GitHub repository URL
          - marketplace_url: Dedalus Marketplace URL
          - language: Programming language (typescript/python)
          - heat_score: Popularity score
          - upvote_count: Number of upvotes
          - tools: List of tools (if include_tools=True)
          - auth_required: Authentication type required (api_key/oauth/none)
        - errors: List of any errors encountered during scanning
    """
    return scan_marketplace_sync(include_tools=include_tools)


server = MCPServer(
    name="dedalus-marketplace-crawler",
    http_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
    streamable_http_stateless=True,
    authorization_server="https://preview.as.dedaluslabs.ai",
)

crawler_tools = [scan_marketplace]


async def main() -> None:
    """Start the MCP server."""
    server.collect(*crawler_tools)
    await server.serve(port=8080)
