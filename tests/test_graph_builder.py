from backend.orchestrator.graph_builder import build_orchestrator_graph

def test_build_graph_compiles():
    graph = build_orchestrator_graph()
    assert graph is not None
    assert hasattr(graph, "get_graph")

def test_erc_feedback_loop():
    graph = build_orchestrator_graph()
    snapshot = graph.get_graph()
    # Graph has 4 agent nodes + __start__ + __end__ = 6 total nodes
    assert len(snapshot.nodes) == 6