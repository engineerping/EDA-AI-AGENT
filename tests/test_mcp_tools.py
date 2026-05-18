import pytest

def test_compdb_search_returns_list():
    from backend.mcp.tools.compdb import compdb_search
    result = compdb_search("STM32", top_k=3)
    assert isinstance(result, list)

def test_file_write_and_read_roundtrip(tmp_path):
    from backend.mcp.tools.file_ops import file_write, file_read
    path = str(tmp_path / "test.txt")
    write_result = file_write(path=path, content="hello world")
    read_result = file_read(path=path)
    assert read_result == "hello world"