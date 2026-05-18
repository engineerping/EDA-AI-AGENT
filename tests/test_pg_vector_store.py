import os
import pytest

def test_search_components_returns_similar():
    # Requires EDB_PG_URL environment variable
    if not os.environ.get("EDB_PG_URL"):
        pytest.skip("EDB_PG_URL not set")
    from backend.db.pg_vector_store import search_components
    results = search_components("STM32F4 32-bit MCU", top_k=3)
    assert isinstance(results, list)
    if results:
        assert "lib_id" in results[0]
        assert "similarity" in results[0]

def test_search_components_returns_empty_for_nonsense():
    if not os.environ.get("EDB_PG_URL"):
        pytest.skip("EDB_PG_URL not set")
    from backend.db.pg_vector_store import search_components
    results = search_components("xyzzyxyzyx", top_k=3)
    assert isinstance(results, list)