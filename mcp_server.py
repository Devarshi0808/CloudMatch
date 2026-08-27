"""Official MCP stdio server for CloudMatch agent integrations."""

from mcp.server.fastmcp import FastMCP

from api.catalog_matcher import search_catalog
from api.open_search import search_open_marketplaces
from api.provider_ingestion import ingest_configured_listings

mcp = FastMCP("CloudMatch")


@mcp.tool()
def search_marketplaces(vendor: str = "", solution: str = "") -> dict:
    """Search official provider APIs with a labeled benchmark fallback."""
    return search_open_marketplaces(vendor, solution)


@mcp.tool()
def catalog_lookup(vendor: str = "", solution: str = "") -> dict:
    """Look up the local seed catalog; this is not a live marketplace search."""
    return search_catalog(vendor, solution)


@mcp.tool()
def ingest_listings(query: str = "") -> dict:
    """Run configured provider listing adapters and return ingestion health metadata."""
    return ingest_configured_listings(query)


if __name__ == "__main__":
    mcp.run()
