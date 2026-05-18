import pytest
from mcp.types import CallToolResult, TextContent

def test_compdb_search_returns_calltoolresult():
    from backend.mcp.tools.compdb import compdb_search
    result = compdb_search("STM32", top_k=3)
    assert isinstance(result, CallToolResult)
    assert isinstance(result.content[0], TextContent)
    assert result.content[0].type == "text"

def test_file_write_and_read_roundtrip(tmp_path):
    from backend.mcp.tools.file_ops import file_write, file_read
    path = str(tmp_path / "test.txt")
    write_result = file_write(path=path, content="hello world")
    assert isinstance(write_result, CallToolResult)
    read_result = file_read(path=path)
    assert isinstance(read_result, CallToolResult)
    assert read_result.content[0].text == "hello world"