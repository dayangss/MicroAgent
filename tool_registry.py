"""micro_agent/tool_registry.py — ToolRegistry: register, find, execute, schema gen."""

import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List


@dataclass
class ToolDefinition:
    name: str
    description: str
    func: Callable[..., str]
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_openai_schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.parameters.get("properties", {}),
                    "required": self.parameters.get("required", []),
                },
            },
        }


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        self._tools[tool.name] = tool

    def register_many(self, tools: List[ToolDefinition]) -> None:
        for t in tools:
            self.register(t)

    def find(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def list_names(self) -> List[str]:
        return list(self._tools.keys())

    def to_openai_schema(self) -> List[Dict[str, Any]]:
        return [t.to_openai_schema() for t in self._tools.values()]

    def execute(self, name: str, args: Dict[str, Any]) -> Any:
        # Returns a ToolResult-like object
        from .messages import ToolResult
        tool = self._tools.get(name)
        if tool is None:
            return ToolResult("", name, f"Unknown tool '{name}'. Available: {self.list_names()}", True)
        try:
            result_str = tool.func(**args)
            return ToolResult("", name, result_str, False)
        except TypeError as e:
            return ToolResult("", name, f"Wrong params for '{name}': {e}. Expected: {json.dumps(tool.parameters, ensure_ascii=False)}", True)
        except Exception as e:
            return ToolResult("", name, f"Tool '{name}' threw an error: {e}", True)

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools
