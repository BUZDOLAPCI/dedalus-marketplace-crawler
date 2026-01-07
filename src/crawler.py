# Copyright (c) 2025 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Marketplace crawler implementation."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

MARKETPLACE_API_URL = "https://www.dedaluslabs.ai/api/marketplace"
MARKETPLACE_BASE_URL = "https://www.dedaluslabs.ai/marketplace"
GITHUB_BASE_URL = "https://github.com"
REQUEST_TIMEOUT = 30
MAX_WORKERS = 5


class ToolInfo(BaseModel):
    """Information about a single MCP tool."""

    name: str
    description: str | None = None


class ServerInfo(BaseModel):
    """Information about a single MCP server in the marketplace."""

    name: str
    slug: str
    publisher: str
    description: str | None = None
    github_url: str | None = None
    marketplace_url: str
    language: str | None = None
    heat_score: int | None = None
    upvote_count: int | None = None
    tools: list[ToolInfo] = Field(default_factory=list)
    auth_required: str | None = None


class ScanResult(BaseModel):
    """Result of the marketplace scan."""

    total_servers: int
    servers: list[ServerInfo]
    errors: list[str] = Field(default_factory=list)


def _fetch_api_data(session: requests.Session) -> dict[str, Any]:
    """Fetch data from the marketplace API."""
    response = session.get(MARKETPLACE_API_URL, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.json()


def _parse_api_server(repo: dict[str, Any]) -> ServerInfo:
    """Parse a server entry from the API response."""
    slug = repo.get("slug", "")
    parts = slug.split("/", 1)
    publisher = parts[0] if len(parts) > 0 else "unknown"
    name = parts[1] if len(parts) > 1 else slug

    # Build GitHub URL from git_slug
    git_slug = repo.get("git_slug")
    github_url = f"{GITHUB_BASE_URL}/{git_slug}" if git_slug else None

    # Extract auth type from tags (handle None explicitly)
    tags = repo.get("tags") or {}
    auth_info = tags.get("auth") or {}
    auth_required = None
    if auth_info.get("api_key"):
        auth_required = "api_key"
    elif auth_info.get("oauth"):
        auth_required = "oauth"
    elif auth_info.get("none"):
        auth_required = "none"

    return ServerInfo(
        name=name,
        slug=slug,
        publisher=publisher,
        description=repo.get("description") or repo.get("subtitle"),
        github_url=github_url,
        marketplace_url=f"{MARKETPLACE_BASE_URL}/{slug}",
        language=tags.get("language"),
        heat_score=repo.get("heat_score"),
        upvote_count=repo.get("upvote_count"),
        auth_required=auth_required,
    )


def _fetch_detail_page(session: requests.Session, url: str) -> str | None:
    """Fetch a detail page HTML."""
    try:
        response = session.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logger.warning("Failed to fetch %s: %s", url, e)
        return None


def _parse_tools_from_html(html: str) -> list[ToolInfo]:
    """Parse tool information from a detail page HTML.

    Note: The live Dedalus marketplace pages load tools dynamically via JavaScript,
    so this function may not find tools from live page fetches. It works with
    server-side rendered or browser-saved HTML that includes the tool content.
    """
    soup = BeautifulSoup(html, "lxml")
    tools = []

    # Common section/footer headers to exclude
    excluded_names = {
        "Tools", "Resources", "Prompts", "Product", "Company", "Legal",
        "Documentation", "Support", "Contact", "About", "Blog", "Pricing",
    }

    # Find tool cards - specifically look for h4 elements within card components
    # that have the right structure (text-lg font-semibold pattern)
    tool_cards = soup.find_all("h4", class_=lambda c: c and "font-semibold" in c and "text-lg" in c)

    for h4 in tool_cards:
        tool_name = h4.get_text(strip=True)

        # Skip if it looks like a section header, not a tool name
        if not tool_name or tool_name in excluded_names:
            continue

        # Skip if it's all uppercase (likely a section header)
        if tool_name.isupper():
            continue

        # Find the description paragraph sibling
        description = None
        next_p = h4.find_next_sibling("p")
        if next_p:
            description = next_p.get_text(strip=True)

        tools.append(ToolInfo(name=tool_name, description=description))

    return tools


def _enrich_with_tools(
    session: requests.Session,
    servers: list[ServerInfo],
    max_workers: int = MAX_WORKERS,
) -> list[str]:
    """Enrich servers with tool information by scraping detail pages."""
    errors = []

    def fetch_tools(server: ServerInfo) -> tuple[ServerInfo, list[ToolInfo] | None, str | None]:
        try:
            html = _fetch_detail_page(session, server.marketplace_url)
            if html:
                tools = _parse_tools_from_html(html)
                return (server, tools, None)
            return (server, None, f"Failed to fetch {server.marketplace_url}")
        except Exception as e:
            return (server, None, f"Error processing {server.slug}: {e}")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_tools, server): server for server in servers}

        for future in as_completed(futures):
            server, tools, error = future.result()
            if error:
                errors.append(error)
                logger.warning(error)
            elif tools is not None:
                server.tools = tools

    return errors


def scan_marketplace_sync(
    include_tools: bool = False,
    session: requests.Session | None = None,
) -> ScanResult:
    """
    Scan the Dedalus Marketplace and return information about all servers.

    Args:
        include_tools: If True, fetch detail pages to extract tool information.
                      This makes the operation slower but provides complete data.
        session: Optional requests session for connection pooling.

    Returns:
        ScanResult containing all server information and any errors encountered.
    """
    if session is None:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "DedalusMarketplaceCrawler/1.0",
            "Accept": "application/json",
        })

    errors: list[str] = []

    # Fetch from API
    try:
        data = _fetch_api_data(session)
    except requests.RequestException as e:
        return ScanResult(
            total_servers=0,
            servers=[],
            errors=[f"Failed to fetch marketplace API: {e}"],
        )

    repositories = data.get("repositories", [])
    servers = [_parse_api_server(repo) for repo in repositories]

    # Optionally enrich with tools from detail pages
    if include_tools and servers:
        tool_errors = _enrich_with_tools(session, servers)
        errors.extend(tool_errors)

    return ScanResult(
        total_servers=len(servers),
        servers=servers,
        errors=errors,
    )
