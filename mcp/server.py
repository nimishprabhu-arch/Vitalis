from fastmcp import FastMCP

from vitalis_tools import get_latest_health_snapshot, summarize_latest_health_snapshot

mcp = FastMCP("Vitalis")


@mcp.tool
def latest_health_snapshot():
    """
    Return the latest Vitalis health snapshot as structured data.
    """
    return get_latest_health_snapshot()


@mcp.tool
def latest_health_summary():
    """
    Return the latest Vitalis health snapshot as a readable summary.
    """
    return summarize_latest_health_snapshot()


if __name__ == "__main__":
    mcp.run()