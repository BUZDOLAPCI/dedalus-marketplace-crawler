# Dedalus Marketplace Crawler

A comprehensive MCP (Model Context Protocol) server that crawls the [Dedalus Marketplace](https://www.dedaluslabs.ai/marketplace) to discover and list all available MCP servers with their metadata.

[![CI](https://github.com/BUZDOLAPCI/dedalus-marketplace-crawler/workflows/CI/badge.svg)](https://github.com/BUZDOLAPCI/dedalus-marketplace-crawler/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **API-Based Discovery**: Uses the public Dedalus Marketplace API (no browser/JavaScript execution required)
- **Comprehensive Metadata**: Extracts names, descriptions, GitHub URLs, languages, and more
- **Concurrent Fetching**: Parallel processing with ThreadPoolExecutor (max 5 workers)
- **Optional Deep Scraping**: Fetch tool information from detail pages when needed
- **Robust Testing**: 97% test coverage with 18 unit tests + 15 integration tests
- **CI/CD**: GitHub Actions workflow with daily integration tests
- **Multi-Python Support**: Compatible with Python 3.10, 3.11, 3.12, and 3.13

## Data Extracted

For each server in the marketplace:

- **Name & Slug**: Server identifier and full slug (publisher/name)
- **Publisher**: Organization or author name
- **GitHub URL**: Link to the source repository
- **Description**: Server description text
- **Language**: Programming language (TypeScript, Python)
- **Heat Score**: Popularity metric (0-100)
- **Upvote Count**: Number of community upvotes
- **Authentication**: Required auth type (api_key, oauth, none)
- **Tools** *(optional)*: List of MCP tools with descriptions

## Installation

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Using uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/BUZDOLAPCI/dedalus-marketplace-crawler.git
cd dedalus-marketplace-crawler

# Install dependencies
uv sync

# Or install with test dependencies
uv sync --group test
```

### Using pip

```bash
# Clone the repository
git clone https://github.com/BUZDOLAPCI/dedalus-marketplace-crawler.git
cd dedalus-marketplace-crawler

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

## Usage

### As an MCP Server

Start the server to expose the `scan_marketplace` tool:

```bash
uv run python src/main.py
```

The server runs on port 8080 by default and provides the `scan_marketplace` tool to AI assistants.

### Direct Python Usage

```python
from src.crawler import scan_marketplace_sync

# Quick scan (without tools)
result = scan_marketplace_sync(include_tools=False)
print(f"Found {result.total_servers} servers")

for server in result.servers:
    print(f"{server.slug}")
    print(f"  GitHub: {server.github_url}")
    print(f"  Language: {server.language}")
    print(f"  Heat: {server.heat_score}")
    print()

# Deep scan (with tools - slower)
result = scan_marketplace_sync(include_tools=True)
for server in result.servers:
    if server.tools:
        print(f"{server.slug} has {len(server.tools)} tools:")
        for tool in server.tools:
            print(f"  - {tool.name}: {tool.description}")
```

### Example Output

```
Found 41 servers

tsion/brave-search-mcp
  GitHub: https://github.com/dedalus-labs/brave-search-mcp
  Language: typescript
  Heat: 99

windsor/ticketmaster-mcp
  GitHub: https://github.com/windsornguyen/ticketmaster-mcp
  Language: typescript
  Heat: 88

akakak/sonar
  GitHub: https://github.com/aryanma/sonar
  Language: typescript
  Heat: 92
```

## Testing

### Unit Tests (Fast, Mocked)

```bash
# Run unit tests with coverage
uv run pytest tests/test_crawler.py -v --cov=src

# All 18 unit tests use mocked requests
# No network calls, fast execution (~1s)
```

### Integration Tests (Live API)

```bash
# Run integration tests against live API
INTEGRATION_TEST=true uv run pytest tests/test_integration.py -v

# 15 integration tests validate:
# - API availability and response structure
# - Data integrity and field validation
# - Response time and performance
```

### Run All Tests

```bash
# Run both unit and integration tests
INTEGRATION_TEST=true uv run pytest tests/ -v --cov=src
```

## API Information

The crawler uses the public Dedalus Marketplace API:

**Endpoint**: `https://www.dedaluslabs.ai/api/marketplace`

**Response Structure**:
```json
{
  "repositories": [
    {
      "repo_id": "...",
      "slug": "publisher/server-name",
      "git_slug": "github-org/repo-name",
      "description": "Server description",
      "language": "typescript",
      "heat_score": 99,
      "upvote_count": 14,
      "tags": {
        "auth": {"api_key": true, "oauth": false, "none": false},
        "language": "typescript",
        "use_cases": {...}
      }
    }
  ]
}
```

## CI/CD

The project uses GitHub Actions for continuous integration:

### Workflows

1. **Lint**: Runs `ruff` for code quality checks
2. **Unit Tests**: Runs mocked tests with coverage reporting
3. **Integration Tests**: Validates against live API (daily schedule + manual trigger)
4. **Test Matrix**: Tests across Python 3.10, 3.11, 3.12, 3.13

### Triggers

- Push to `main`/`master`
- Pull requests
- **Daily at 6 AM UTC** (monitors for API changes)
- Manual dispatch

### Test Coverage

Current coverage: **97%** (unit tests)

## Development

### Project Structure

```
dedalus-marketplace-crawler/
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions workflow
├── src/
│   ├── __init__.py
│   ├── crawler.py              # Core crawler logic
│   ├── server.py               # MCP server implementation
│   └── main.py                 # Entry point
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Test fixtures
│   ├── test_crawler.py         # Unit tests (18 tests)
│   └── test_integration.py     # Integration tests (15 tests)
├── examples/
│   └── dedaluslabs-ai-marketplace-akakak-sonar.html
├── pyproject.toml              # Project configuration
├── .python-version             # Python version (3.12)
└── README.md
```

### Running Locally

```bash
# Install dev dependencies
uv sync --group dev

# Run linting
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/

# Run tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_crawler.py::TestParseApiServer -v
```

### Code Quality

The project uses:
- **ruff**: Linting and formatting
- **pytest**: Testing framework
- **pytest-cov**: Coverage reporting
- **requests-mock**: HTTP mocking for unit tests
- **mypy-compatible**: Type hints throughout

## Performance

- **Basic Scan** (without tools): ~1-2 seconds for 41 servers
- **Deep Scan** (with tools): ~5-10 seconds (concurrent fetching with 5 workers)
- **API Response Time**: Typically < 2 seconds
- **Memory Usage**: < 50 MB for full scan

## Limitations

- **Tool Extraction**: The live marketplace pages load tool information via JavaScript. The tool extraction feature works best with browser-rendered HTML or server-side rendered pages.
- **Rate Limiting**: The crawler respects the marketplace API and doesn't implement aggressive rate limiting. For production use, consider adding rate limiting.
- **Authentication**: No authentication required for the public marketplace API.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Run the test suite (`uv run pytest tests/ -v`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Guidelines

- Maintain test coverage above 95%
- Follow existing code style (ruff will check)
- Add integration tests for API-related changes
- Update documentation for new features

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Dedalus MCP](https://docs.dedaluslabs.ai/) framework
- Inspired by the [Dedalus Python Template](https://github.com/dedalus-labs/example-dedalus-mcp)
- Crawls the [Dedalus Marketplace](https://www.dedaluslabs.ai/marketplace)

## Links

- **Dedalus Labs**: https://www.dedaluslabs.ai/
- **Dedalus Marketplace**: https://www.dedaluslabs.ai/marketplace
- **Dedalus Documentation**: https://docs.dedaluslabs.ai/
- **MCP Specification**: https://modelcontextprotocol.io/

---

**🤖 Generated with [Claude Code](https://claude.com/claude-code)**
