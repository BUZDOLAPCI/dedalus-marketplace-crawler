#!/usr/bin/env python3
# Copyright (c) 2025 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Dedalus entry point wrapper for the Marketplace Crawler MCP server."""

from __future__ import annotations

import asyncio
import os
import sys


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from server import main as server_main  # noqa: E402


def main() -> int:
    """Run the MCP server using the Dedalus entry point."""
    asyncio.run(server_main())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
