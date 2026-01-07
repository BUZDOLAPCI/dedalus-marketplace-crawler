# Copyright (c) 2025 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Pytest configuration and fixtures."""

import pytest
import requests


@pytest.fixture
def mock_api_response() -> dict:
    """Mock response from the marketplace API."""
    return {
        "repositories": [
            {
                "repo_id": "test-repo-1",
                "org_id": "test-org-1",
                "slug": "testpub/test-server",
                "git_slug": "testpub/test-server-repo",
                "title": "Test Server",
                "subtitle": "A test MCP server",
                "description": "This is a comprehensive test server for testing purposes.",
                "visibility": "public",
                "upvote_count": 10,
                "heat_score": 85,
                "created_at": "2025-01-01T00:00:00.000000+00:00",
                "tags": {
                    "auth": {"none": False, "oauth": False, "api_key": True},
                    "language": "python",
                    "verified": True,
                    "use_cases": {"search": True, "database": False},
                },
                "isOwner": False,
            },
            {
                "repo_id": "test-repo-2",
                "org_id": "test-org-2",
                "slug": "anotherpub/another-server",
                "git_slug": "anotherpub/another-repo",
                "title": None,
                "subtitle": "Another server subtitle",
                "description": None,
                "visibility": "public",
                "upvote_count": 5,
                "heat_score": 50,
                "created_at": "2025-01-02T00:00:00.000000+00:00",
                "tags": {
                    "auth": {"none": True, "oauth": False, "api_key": False},
                    "language": "typescript",
                    "verified": False,
                    "use_cases": {},
                },
                "isOwner": False,
            },
        ]
    }


@pytest.fixture
def mock_detail_page_with_tools() -> str:
    """Mock HTML for a detail page with tools (browser-rendered version)."""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Test Server</title></head>
    <body>
        <h2 class="text-foreground text-2xl font-bold break-words">test-server</h2>
        <p class="text-muted-foreground text-sm leading-relaxed pt-1">
            This is a test server description.
        </p>
        <div class="space-y-3">
            <div data-slot="card">
                <h4 class="text-lg font-semibold break-words overflow-wrap-anywhere">test_tool_one</h4>
                <p class="text-muted-foreground text-sm leading-relaxed">
                    First test tool description.
                </p>
            </div>
            <div data-slot="card">
                <h4 class="text-lg font-semibold break-words overflow-wrap-anywhere">test_tool_two</h4>
                <p class="text-muted-foreground text-sm leading-relaxed">
                    Second test tool description.
                </p>
            </div>
        </div>
        <footer>
            <h4 class="mb-4 text-sm font-semibold uppercase">Product</h4>
            <h4 class="mb-4 text-sm font-semibold uppercase">Company</h4>
            <h4 class="mb-4 text-sm font-semibold uppercase">Legal</h4>
        </footer>
    </body>
    </html>
    """


@pytest.fixture
def mock_detail_page_without_tools() -> str:
    """Mock HTML for a detail page without tools section."""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Another Server</title></head>
    <body>
        <h2 class="text-foreground text-2xl font-bold break-words">another-server</h2>
        <p class="text-muted-foreground text-sm leading-relaxed pt-1">
            This server has no tools.
        </p>
    </body>
    </html>
    """


@pytest.fixture
def requests_session() -> requests.Session:
    """Create a requests session for testing."""
    session = requests.Session()
    session.headers.update({"User-Agent": "TestCrawler/1.0", "Accept": "application/json"})
    return session
