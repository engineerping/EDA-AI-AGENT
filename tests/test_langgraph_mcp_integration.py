"""Integration test: LangGraph state machine wired to MCP via ToolNode."""
import pytest
from backend.orchestrator.graph_builder import build_orchestrator_graph
from backend.agents.design_agent import build_design_agent_graph


def test_orchestrator_graph_builds():
    """Orchestrator graph compiles without errors."""
    graph = build_orchestrator_graph()
    assert graph is not None
    assert hasattr(graph, "get_graph")


def test_design_agent_graph_builds_with_mcp_tools():
    """DesignAgent sub-graph wires MCP compdb tools via ToolNode."""
    graph = build_design_agent_graph()
    assert graph is not None
    snapshot = graph.get_graph()
    # design_tools node + start + end = 3 nodes
    assert len(snapshot.nodes) == 3
    # Verify compdb_search and compdb_add are accessible
    from backend.mcp.tools.compdb import compdb_search, compdb_add
    assert callable(compdb_search)
    assert callable(compdb_add)


def test_mcp_client_can_search_components():
    """Verify MCP tools (compdb_search, compdb_add) are registered and callable."""
    from backend.mcp.tools.compdb import compdb_search, compdb_add
    from mcp.types import CallToolResult
    # Verify tools are callable and return CallToolResult
    assert callable(compdb_search)
    assert callable(compdb_add)
    # compdb_search returns CallToolResult when called with valid args
    result = compdb_search(query="capacitor", top_k=3)
    assert isinstance(result, CallToolResult)
    # Verify the content contains search results
    assert len(result.content) > 0