"""Entry points: --serve runs the Starlette backend; stdio serves MCP directly.

Both transports share the same in-process fan-out and the same SQLite-WAL
health ledger (short transactions, no shared handles), so stdio works fully
standalone and HTTP serves the webapp + fleet consumers on the backend port.
"""

from __future__ import annotations

import argparse
import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
# Queries live in provider URLs - keep them out of stderr/MCP logs (issue #1.4).
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="super-search-mcp")
    parser.add_argument("--serve", action="store_true", help="run the HTTP backend (REST + /mcp)")
    parser.add_argument("--port", type=int, default=0, help="backend port (default: env or 11226)")
    parser.add_argument(
        "--stdio", action="store_true", help="run MCP over stdio (default without --serve)"
    )
    args = parser.parse_args(argv)

    if args.serve:
        import uvicorn

        from .backend import build_app
        from .config import settings

        port = args.port or settings.backend_port
        uvicorn.run(build_app(), host="127.0.0.1", port=port, log_level="info", access_log=False)
        return 0

    from .server import mcp

    mcp.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
