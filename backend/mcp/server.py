"""MCP Server for EDA-AI-Agent."""
import asyncio
from mcp.server import Server
from mcp.types import Tool, CallToolResult, TextContent

server = Server("eda-tools")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="compdb_search",
            description="Search electronic component database with natural language query",
            inputSchema={"type": "object", "properties": {"query": {"type": "string"}, "top_k": {"type": "integer", "default": 5}}}
        ),
        Tool(
            name="compdb_add",
            description="Add a component to the database",
            inputSchema={"type": "object", "properties": {"name": {"type": "string"}, "category": {"type": "string"}, "description": {"type": "string"}}}
        ),
        Tool(
            name="kicad_erc",
            description="Run KiCad ERC on a schematic file",
            inputSchema={"type": "object", "properties": {"schematic_path": {"type": "string"}}}
        ),
        Tool(
            name="kicad_generate_sch",
            description="Generate a KiCad .kicad_sch file from BOM",
            inputSchema={"type": "object", "properties": {"bom": {"type": "array"}, "output_path": {"type": "string"}}}
        ),
        Tool(
            name="file_write",
            description="Write content to a file",
            inputSchema={"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}}
        ),
        Tool(
            name="file_read",
            description="Read content from a file",
            inputSchema={"type": "object", "properties": {"path": {"type": "string"}}}
        ),
    ]

@server.call_tool()
async def call_tool(name: str, args: dict) -> CallToolResult:
    from backend.mcp.tools import compdb, kicad, file_ops
    handlers = {
        "compdb_search": compdb.compdb_search,
        "compdb_add": compdb.compdb_add,
        "kicad_erc": kicad.kicad_erc,
        "kicad_generate_sch": kicad.kicad_generate_sch,
        "file_write": file_ops.file_write,
        "file_read": file_ops.file_read,
    }
    if name not in handlers:
        return CallToolResult(isError=True, content=[TextContent(type="text", text=f"Unknown tool: {name}")])
    result = handlers[name](**args)
    if asyncio.iscoroutine(result):
        result = await result
    # Wrap result in CallToolResult
    if isinstance(result, CallToolResult):
        return result
    if isinstance(result, str):
        return CallToolResult(content=[TextContent(type="text", text=result)])
    if isinstance(result, list):
        return CallToolResult(content=[TextContent(type="text", text=str(result))])
    return CallToolResult(content=[TextContent(type="text", text=str(result))])

async def main():
    async with server.run_session():
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())