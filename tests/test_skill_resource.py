"""Skill resource test: skill://super-search is registered and readable."""

from fastmcp import Client

from super_search_mcp.server import mcp


async def test_skill_resource_registered_and_readable() -> None:
    async with Client(mcp) as client:
        resources = await client.list_resources()
        uris = [str(r.uri) for r in resources]
        assert "skill://super-search" in uris
        content = await client.read_resource("skill://super-search")
        assert isinstance(content, list) and len(content) > 0
        text = "".join(
            getattr(block, "text", "") for block in content if hasattr(block, "text")
        )
        assert "SearchStudio" in text
