# Copyright (c) 2025 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Entry point for the Dedalus Marketplace Crawler MCP server."""

import asyncio

from dotenv import load_dotenv

from server import main

load_dotenv()


if __name__ == "__main__":
    asyncio.run(main())
