"""
BaseAgent: async LiteLLM tool-call loop with token streaming.

Each subclass defines system_prompt and tools. Call agent.run(messages, on_token).
The loop continues until the LLM returns a non-tool-call response (text finish)
or calls the agent's designated finalize tool.

Tool functions are plain Python callables registered with @agent.tool().
Tools that need to pause execution (ask_user) are declared as async and may await
an external queue.
"""
from __future__ import annotations
import inspect, json, logging
from collections.abc import AsyncGenerator, Callable
from typing import Any

import litellm

from backend.config import load_config

logger = logging.getLogger("eda-agent.agent")


class ToolCallError(Exception):
    pass


class BaseAgent:
    system_prompt: str = ""
    finalize_tool: str = ""  # name of the tool whose call signals completion

    def __init__(self) -> None:
        self._tools: dict[str, Callable] = {}
        self._tool_schemas: list[dict] = []

    def tool(self, fn: Callable) -> Callable:
        name = fn.__name__
        doc = (fn.__doc__ or "").strip().split("\n")[0]
        sig = inspect.signature(fn)
        props: dict[str, Any] = {}
        required: list[str] = []
        for pname, param in sig.parameters.items():
            if pname in ("self", "session"):
                continue
            ann = param.annotation
            json_type = {str: "string", int: "integer", float: "number", bool: "boolean", list: "array"}.get(ann, "string")
            props[pname] = {"type": json_type, "description": pname}
            if param.default is inspect.Parameter.empty:
                required.append(pname)
        self._tool_schemas.append({
            "type": "function",
            "function": {"name": name, "description": doc, "parameters": {"type": "object", "properties": props, "required": required}},
        })
        self._tools[name] = fn
        return fn

    async def run(
        self,
        messages: list[dict],
        on_token: Callable[[str], None] | None = None,
        extra_kwargs: dict | None = None,
    ) -> str:
        """Run the tool-call loop. Returns final text response or finalize tool args as JSON."""
        cfg = load_config()
        agent_name = self.__class__.__name__
        logger.info("[%s] Starting (model=%s)", agent_name, cfg.model)
        kwargs: dict[str, Any] = {
            "model": cfg.model,
            "messages": [{"role": "system", "content": self.system_prompt}] + messages,
            "tools": self._tool_schemas,
            "stream": True,
        }
        if cfg.api_key:
            kwargs["api_key"] = cfg.api_key
        if cfg.base_url:
            kwargs["base_url"] = cfg.base_url
        if extra_kwargs:
            kwargs.update(extra_kwargs)

        MAX_ITERS = 20
        for i in range(1, MAX_ITERS + 1):
            logger.info("[%s] LLM call iter %d/%d", agent_name, i, MAX_ITERS)
            collected_text = ""
            tool_calls_buffer: dict[int, dict] = {}

            response = await litellm.acompletion(**kwargs)
            async for chunk in response:
                delta = chunk.choices[0].delta
                if delta.content:
                    collected_text += delta.content
                    if on_token:
                        on_token(delta.content)
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in tool_calls_buffer:
                            tool_calls_buffer[idx] = {"id": tc.id or "", "name": "", "args": "", "index": idx}
                        if tc.function.name:
                            tool_calls_buffer[idx]["name"] = tc.function.name
                        if tc.function.arguments:
                            tool_calls_buffer[idx]["args"] += tc.function.arguments

            if not tool_calls_buffer:
                logger.info("[%s] No tool calls — returning text (len=%d)", agent_name, len(collected_text))
                return collected_text

            # Execute tool calls
            tool_results = []
            for tc in sorted(tool_calls_buffer.values(), key=lambda x: x["index"]):
                name, args_str = tc["name"], tc["args"]
                args = json.loads(args_str) if args_str.strip() else {}
                fn = self._tools.get(name)
                if fn is None:
                    result = f"Error: unknown tool '{name}'"
                    logger.warning("[%s] Unknown tool: %s", agent_name, name)
                else:
                    try:
                        if inspect.iscoroutinefunction(fn):
                            result = await fn(**args)
                        else:
                            result = fn(**args)
                    except Exception as e:
                        raise ToolCallError(f"Tool '{name}' raised: {e}") from e
                logger.info("[%s] Tool '%s' executed", agent_name, name)

                result_str = json.dumps(result) if not isinstance(result, str) else result
                tool_results.append({"tool_call_id": tc["id"], "name": name, "content": result_str, "args": args_str})

                if name == self.finalize_tool:
                    logger.info("[%s] Finalize tool '%s' reached — returning", agent_name, name)
                    return result_str

            # Append assistant + tool results to messages for next iteration
            kwargs["messages"].append({"role": "assistant", "content": collected_text or None,
                                       "tool_calls": [{"id": t["tool_call_id"], "type": "function",
                                                        "function": {"name": t["name"], "arguments": t["args"]}}
                                                       for t in tool_results]})
            for tr in tool_results:
                kwargs["messages"].append({"role": "tool", "tool_call_id": tr["tool_call_id"], "content": tr["content"]})

        logger.warning("[%s] Max iterations reached", agent_name)
        return "Max iterations reached."
