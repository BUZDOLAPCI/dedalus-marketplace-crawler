# Copyright (c) 2025 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Integration tests that hit the live Dedalus Marketplace API.

These tests are designed to:
1. Verify the crawler works against the real API
2. Detect breaking changes in the API response structure
3. Monitor API availability

Run with: pytest tests/test_integration.py -v
"""

import os
import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from crawler import (
    GITHUB_BASE_URL,
    MARKETPLACE_API_URL,
    MARKETPLACE_BASE_URL,
    ScanResult,
    scan_marketplace_sync,
)

# Skip integration tests unless explicitly enabled
pytestmark = pytest.mark.skipif(
    os.environ.get("INTEGRATION_TEST") != "true",
    reason="Integration tests require INTEGRATION_TEST=true",
)


class TestLiveMarketplaceAPI:
    """Integration tests against the live Dedalus Marketplace API."""

    def test_api_returns_servers(self) -> None:
        """Test that the API returns a non-empty list of servers."""
        result = scan_marketplace_sync(include_tools=False)

        assert isinstance(result, ScanResult)
        assert result.total_servers > 0, "Expected at least one server in marketplace"
        assert len(result.servers) == result.total_servers

    def test_api_returns_no_errors(self) -> None:
        """Test that the API scan completes without errors."""
        result = scan_marketplace_sync(include_tools=False)

        assert len(result.errors) == 0, f"Unexpected errors: {result.errors}"

    def test_server_has_required_fields(self) -> None:
        """Test that servers have all required fields populated."""
        result = scan_marketplace_sync(include_tools=False)

        assert result.total_servers > 0, "Need at least one server to test"

        for server in result.servers:
            # Required fields
            assert server.name, f"Server missing name: {server}"
            assert server.slug, f"Server missing slug: {server}"
            assert server.publisher, f"Server missing publisher: {server}"
            assert server.marketplace_url, f"Server missing marketplace_url: {server}"

            # Validate URL formats
            assert server.marketplace_url.startswith(MARKETPLACE_BASE_URL), (
                f"Invalid marketplace URL: {server.marketplace_url}"
            )

    def test_servers_have_github_urls(self) -> None:
        """Test that most servers have GitHub URLs."""
        result = scan_marketplace_sync(include_tools=False)

        servers_with_github = [s for s in result.servers if s.github_url]

        # Expect at least 50% of servers to have GitHub URLs
        min_expected = result.total_servers // 2
        assert len(servers_with_github) >= min_expected, (
            f"Expected at least {min_expected} servers with GitHub URLs, "
            f"got {len(servers_with_github)}"
        )

        # Validate GitHub URL format
        for server in servers_with_github:
            assert server.github_url.startswith(GITHUB_BASE_URL), (
                f"Invalid GitHub URL format: {server.github_url}"
            )

    def test_slug_format(self) -> None:
        """Test that server slugs have the expected publisher/name format."""
        result = scan_marketplace_sync(include_tools=False)

        for server in result.servers:
            # Slug should be in format "publisher/name"
            assert "/" in server.slug, f"Slug missing separator: {server.slug}"

            parts = server.slug.split("/")
            assert len(parts) == 2, f"Invalid slug format: {server.slug}"
            assert parts[0] == server.publisher, (
                f"Slug publisher mismatch: {server.slug} vs {server.publisher}"
            )

    def test_marketplace_url_matches_slug(self) -> None:
        """Test that marketplace URLs are correctly formed from slugs."""
        result = scan_marketplace_sync(include_tools=False)

        for server in result.servers:
            expected_url = f"{MARKETPLACE_BASE_URL}/{server.slug}"
            assert server.marketplace_url == expected_url, (
                f"URL mismatch: {server.marketplace_url} != {expected_url}"
            )

    def test_known_servers_exist(self) -> None:
        """Test that some known servers are present in the marketplace."""
        result = scan_marketplace_sync(include_tools=False)

        slugs = {s.slug for s in result.servers}

        # These are servers that should exist based on examples
        # Update this list if servers are removed from marketplace
        known_servers = [
            "windsor/ticketmaster-mcp",
            "windsor/open-meteo-mcp",
        ]

        found = [s for s in known_servers if s in slugs]
        assert len(found) > 0, (
            f"Expected to find at least one known server. "
            f"Known: {known_servers}, Found slugs sample: {list(slugs)[:10]}"
        )

    def test_language_field_values(self) -> None:
        """Test that language field contains expected values."""
        result = scan_marketplace_sync(include_tools=False)

        servers_with_language = [s for s in result.servers if s.language]
        assert len(servers_with_language) > 0, "Expected some servers with language"

        valid_languages = {"typescript", "python"}
        for server in servers_with_language:
            assert server.language in valid_languages, (
                f"Unexpected language '{server.language}' for {server.slug}"
            )

    def test_heat_score_range(self) -> None:
        """Test that heat scores are within expected range."""
        result = scan_marketplace_sync(include_tools=False)

        servers_with_score = [s for s in result.servers if s.heat_score is not None]
        assert len(servers_with_score) > 0, "Expected some servers with heat scores"

        for server in servers_with_score:
            assert 0 <= server.heat_score <= 100, (
                f"Heat score out of range for {server.slug}: {server.heat_score}"
            )

    def test_upvote_count_non_negative(self) -> None:
        """Test that upvote counts are non-negative."""
        result = scan_marketplace_sync(include_tools=False)

        for server in result.servers:
            if server.upvote_count is not None:
                assert server.upvote_count >= 0, (
                    f"Negative upvotes for {server.slug}: {server.upvote_count}"
                )

    def test_auth_field_values(self) -> None:
        """Test that auth_required field contains expected values."""
        result = scan_marketplace_sync(include_tools=False)

        servers_with_auth = [s for s in result.servers if s.auth_required]
        # Not all servers may have auth info, so just validate those that do

        valid_auth_types = {"api_key", "oauth", "none"}
        for server in servers_with_auth:
            assert server.auth_required in valid_auth_types, (
                f"Unexpected auth type '{server.auth_required}' for {server.slug}"
            )


class TestAPIStability:
    """Tests to detect API changes that could break the crawler."""

    def test_api_endpoint_accessible(self) -> None:
        """Test that the API endpoint is accessible."""
        import requests

        response = requests.get(MARKETPLACE_API_URL, timeout=30)
        assert response.status_code == 200, (
            f"API returned status {response.status_code}"
        )

    def test_api_returns_json(self) -> None:
        """Test that the API returns valid JSON."""
        import requests

        response = requests.get(MARKETPLACE_API_URL, timeout=30)
        data = response.json()

        assert isinstance(data, dict), "Expected JSON object"
        assert "repositories" in data, "Missing 'repositories' key in response"

    def test_repository_schema(self) -> None:
        """Test that repository objects have expected schema."""
        import requests

        response = requests.get(MARKETPLACE_API_URL, timeout=30)
        data = response.json()

        repos = data.get("repositories", [])
        assert len(repos) > 0, "No repositories in response"

        # Check first repo has expected fields
        repo = repos[0]
        expected_fields = ["slug", "git_slug", "description", "visibility"]

        for field in expected_fields:
            assert field in repo, f"Missing field '{field}' in repository schema"

    def test_response_time(self) -> None:
        """Test that API responds within acceptable time."""
        import time

        import requests

        start = time.time()
        response = requests.get(MARKETPLACE_API_URL, timeout=30)
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 10, f"API response too slow: {elapsed:.2f}s"
