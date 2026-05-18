from backend.agents.req_agent.agent_graph import build_req_agent_graph

def test_req_agent_graph_builds():
    graph = build_req_agent_graph()
    assert graph is not None

def test_req_agent_graph_has_nodes():
    graph = build_req_agent_graph()
    snapshot = graph.get_graph()
    # Should have ask_question and finalize nodes
    node_names = set(snapshot.nodes)
    assert len(node_names) >= 2