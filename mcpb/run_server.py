"""MCPB bootstrap: run the bundled package over stdio.

Executed by the pack launch-check via runpy (run_name != __main__) and by
Claude Desktop as the bundle entry point. Puts bundled src/ on sys.path so
package-relative imports resolve inside the bundle, then starts the MCP
server. No network, no side effects at import beyond tool registration.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from super_search_mcp.server import mcp  # noqa: E402

if __name__ == "__main__":
    mcp.run()
