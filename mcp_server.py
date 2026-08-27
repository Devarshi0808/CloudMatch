"""Native stdio MCP server for grounded marketplace research."""
from mcp.server.fastmcp import FastMCP
from api.agent_research import compare_products as compare, research_products as research
from api.catalog_matcher import search_catalog
from api.evidence_store import get_evidence as inspect_evidence
from api.open_search import search_open_marketplaces
mcp = FastMCP("CloudMatch")

@mcp.tool()
def search_marketplaces(vendor: str = "", solution: str = "") -> dict:
    """Search reviewed evidence with a labeled benchmark fallback."""
    return search_open_marketplaces(vendor, solution)
@mcp.tool()
def research_products(request: str) -> dict:
    """Create a grounded research brief or explicitly abstain."""
    return research(request)
@mcp.tool()
def compare_products(request: str) -> dict:
    """Compare grounded candidates and disclose incomplete evidence."""
    return compare(request)
@mcp.tool()
def get_evidence(evidence_id: str) -> dict:
    """Inspect one stable evidence record."""
    return inspect_evidence(evidence_id) or {"error":"evidence_not_found"}
@mcp.tool()
def catalog_lookup(vendor: str = "", solution: str = "") -> dict:
    """Rank the benchmark catalog; this is not live marketplace data."""
    return search_catalog(vendor, solution)
if __name__ == "__main__": mcp.run()
