# Copyright (c) 2025 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Tests for the marketplace crawler."""

import sys
from pathlib import Path

import requests
import requests_mock as rm

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from crawler import (
    MARKETPLACE_API_URL,
    MARKETPLACE_BASE_URL,
    ScanResult,
    ServerInfo,
    ToolInfo,
    _parse_api_server,
    _parse_tools_from_html,
    scan_marketplace_sync,
)


class TestParseApiServer:
    """Tests for _parse_api_server function."""

    def test_parse_basic_server(self) -> None:
        """Test parsing a basic server entry from API."""
        repo = {
            "slug": "publisher/server-name",
            "git_slug": "publisher/server-repo",
            "description": "Test description",
            "heat_score": 80,
            "upvote_count": 15,
            "tags": {
                "language": "python",
                "auth": {"api_key": True, "oauth": False, "none": False},
            },
        }

        result = _parse_api_server(repo)

        assert result.name == "server-name"
        assert result.slug == "publisher/server-name"
        assert result.publisher == "publisher"
        assert result.description == "Test description"
        assert result.github_url == "https://github.com/publisher/server-repo"
        assert result.marketplace_url == f"{MARKETPLACE_BASE_URL}/publisher/server-name"
        assert result.language == "python"
        assert result.heat_score == 80
        assert result.upvote_count == 15
        assert result.auth_required == "api_key"

    def test_parse_server_with_subtitle_fallback(self) -> None:
        """Test that subtitle is used when description is missing."""
        repo = {
            "slug": "pub/srv",
            "git_slug": "pub/srv",
            "description": None,
            "subtitle": "Subtitle description",
            "tags": {},
        }

        result = _parse_api_server(repo)

        assert result.description == "Subtitle description"

    def test_parse_server_without_github(self) -> None:
        """Test parsing server without git_slug."""
        repo = {
            "slug": "pub/srv",
            "git_slug": None,
            "tags": {},
        }

        result = _parse_api_server(repo)

        assert result.github_url is None

    def test_parse_server_oauth_auth(self) -> None:
        """Test parsing server with OAuth authentication."""
        repo = {
            "slug": "pub/srv",
            "git_slug": "pub/srv",
            "tags": {"auth": {"oauth": True, "api_key": False, "none": False}},
        }

        result = _parse_api_server(repo)

        assert result.auth_required == "oauth"

    def test_parse_server_no_auth(self) -> None:
        """Test parsing server with no authentication required."""
        repo = {
            "slug": "pub/srv",
            "git_slug": "pub/srv",
            "tags": {"auth": {"none": True, "oauth": False, "api_key": False}},
        }

        result = _parse_api_server(repo)

        assert result.auth_required == "none"


class TestParseToolsFromHtml:
    """Tests for _parse_tools_from_html function."""

    def test_parse_tools_from_valid_html(self, mock_detail_page_with_tools: str) -> None:
        """Test parsing tools from HTML with tool cards."""
        tools = _parse_tools_from_html(mock_detail_page_with_tools)

        assert len(tools) == 2
        assert tools[0].name == "test_tool_one"
        assert tools[0].description == "First test tool description."
        assert tools[1].name == "test_tool_two"
        assert tools[1].description == "Second test tool description."

    def test_parse_tools_from_html_without_tools(self, mock_detail_page_without_tools: str) -> None:
        """Test parsing HTML page that has no tools."""
        tools = _parse_tools_from_html(mock_detail_page_without_tools)

        assert len(tools) == 0

    def test_parse_tools_excludes_section_headers(self) -> None:
        """Test that section headers like 'Tools' are excluded from results."""
        html = """
        <html>
        <body>
            <h4 class="text-lg font-semibold">Tools</h4>
            <h4 class="text-lg font-semibold">actual_tool</h4>
            <p>Tool description</p>
            <h4 class="text-sm font-semibold uppercase">Product</h4>
        </body>
        </html>
        """

        tools = _parse_tools_from_html(html)

        assert len(tools) == 1
        assert tools[0].name == "actual_tool"


class TestScanMarketplaceSync:
    """Tests for scan_marketplace_sync function."""

    def test_scan_without_tools(
        self,
        mock_api_response: dict,
        requests_session: requests.Session,
    ) -> None:
        """Test scanning marketplace without fetching tools."""
        with rm.Mocker() as m:
            m.get(MARKETPLACE_API_URL, json=mock_api_response)

            result = scan_marketplace_sync(include_tools=False, session=requests_session)

            assert result.total_servers == 2
            assert len(result.servers) == 2
            assert len(result.errors) == 0

            # Check first server
            server1 = result.servers[0]
            assert server1.name == "test-server"
            assert server1.publisher == "testpub"
            assert server1.github_url == "https://github.com/testpub/test-server-repo"
            assert server1.language == "python"
            assert server1.auth_required == "api_key"
            assert server1.tools == []  # No tools fetched

            # Check second server
            server2 = result.servers[1]
            assert server2.name == "another-server"
            assert server2.publisher == "anotherpub"
            assert server2.auth_required == "none"

    def test_scan_with_tools(
        self,
        mock_api_response: dict,
        mock_detail_page_with_tools: str,
        mock_detail_page_without_tools: str,
        requests_session: requests.Session,
    ) -> None:
        """Test scanning marketplace with tool fetching enabled."""
        with rm.Mocker() as m:
            m.get(MARKETPLACE_API_URL, json=mock_api_response)
            m.get(
                f"{MARKETPLACE_BASE_URL}/testpub/test-server",
                text=mock_detail_page_with_tools,
            )
            m.get(
                f"{MARKETPLACE_BASE_URL}/anotherpub/another-server",
                text=mock_detail_page_without_tools,
            )

            result = scan_marketplace_sync(include_tools=True, session=requests_session)

            assert result.total_servers == 2
            assert len(result.errors) == 0

            # First server should have tools
            server1 = result.servers[0]
            assert len(server1.tools) == 2
            assert server1.tools[0].name == "test_tool_one"

            # Second server should have no tools
            server2 = result.servers[1]
            assert len(server2.tools) == 0

    def test_scan_handles_api_failure(self, requests_session: requests.Session) -> None:
        """Test that API failure is handled gracefully."""
        with rm.Mocker() as m:
            m.get(MARKETPLACE_API_URL, status_code=500)

            result = scan_marketplace_sync(include_tools=False, session=requests_session)

            assert result.total_servers == 0
            assert len(result.servers) == 0
            assert len(result.errors) == 1
            assert "Failed to fetch marketplace API" in result.errors[0]

    def test_scan_handles_detail_page_failure(
        self,
        mock_api_response: dict,
        mock_detail_page_with_tools: str,
        requests_session: requests.Session,
    ) -> None:
        """Test that detail page failures don't crash the entire scan."""
        with rm.Mocker() as m:
            m.get(MARKETPLACE_API_URL, json=mock_api_response)
            m.get(
                f"{MARKETPLACE_BASE_URL}/testpub/test-server",
                text=mock_detail_page_with_tools,
            )
            # Second detail page fails
            m.get(
                f"{MARKETPLACE_BASE_URL}/anotherpub/another-server",
                status_code=404,
            )

            result = scan_marketplace_sync(include_tools=True, session=requests_session)

            # Should still return both servers
            assert result.total_servers == 2
            assert len(result.servers) == 2

            # First server should have tools
            assert len(result.servers[0].tools) == 2

            # Error should be logged
            assert len(result.errors) == 1
            assert "another-server" in result.errors[0] or "Failed" in result.errors[0]

    def test_scan_empty_marketplace(self, requests_session: requests.Session) -> None:
        """Test scanning an empty marketplace."""
        with rm.Mocker() as m:
            m.get(MARKETPLACE_API_URL, json={"repositories": []})

            result = scan_marketplace_sync(include_tools=False, session=requests_session)

            assert result.total_servers == 0
            assert len(result.servers) == 0
            assert len(result.errors) == 0

    def test_scan_creates_session_if_not_provided(self, mock_api_response: dict) -> None:
        """Test that a session is created if none is provided."""
        with rm.Mocker() as m:
            m.get(MARKETPLACE_API_URL, json=mock_api_response)

            result = scan_marketplace_sync(include_tools=False, session=None)

            assert result.total_servers == 2


class TestServerInfoModel:
    """Tests for the ServerInfo Pydantic model."""

    def test_server_info_defaults(self) -> None:
        """Test ServerInfo with minimal required fields."""
        server = ServerInfo(
            name="test",
            slug="pub/test",
            publisher="pub",
            marketplace_url="https://example.com",
        )

        assert server.description is None
        assert server.github_url is None
        assert server.language is None
        assert server.tools == []

    def test_server_info_serialization(self) -> None:
        """Test ServerInfo JSON serialization."""
        server = ServerInfo(
            name="test",
            slug="pub/test",
            publisher="pub",
            marketplace_url="https://example.com",
            tools=[ToolInfo(name="tool1", description="desc")],
        )

        data = server.model_dump()

        assert data["name"] == "test"
        assert len(data["tools"]) == 1
        assert data["tools"][0]["name"] == "tool1"


class TestScanResultModel:
    """Tests for the ScanResult Pydantic model."""

    def test_scan_result_defaults(self) -> None:
        """Test ScanResult with minimal fields."""
        result = ScanResult(total_servers=0, servers=[])

        assert result.errors == []

    def test_scan_result_with_errors(self) -> None:
        """Test ScanResult with errors."""
        result = ScanResult(
            total_servers=1,
            servers=[
                ServerInfo(
                    name="test",
                    slug="pub/test",
                    publisher="pub",
                    marketplace_url="https://example.com",
                )
            ],
            errors=["Error 1", "Error 2"],
        )

        assert len(result.errors) == 2
