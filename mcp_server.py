"""Native stdio MCP server for grounded marketplace research."""
from mcp.server.fastmcp import FastMCP
from api.agent_research import compare_products as compare, research_products as research
from api.open_search import search_open_marketplaces
mcp = FastMCP("CloudMatch")

@mcp.tool()
def search_marketplaces(vendor: str = "", solution: str = "") -> dict:
    """Search current public results restricted to official marketplace domains."""
    return search_open_marketplaces(vendor, solution)
@mcp.tool()
def research_products(request: str) -> dict:
    """Create a grounded research brief or explicitly abstain."""
    return research(request)
@mcp.tool()
def compare_products(request: str) -> dict:
    """Compare grounded candidates and disclose incomplete evidence."""
    return compare(request)
if __name__ == "__main__": mcp.run()
