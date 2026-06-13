"""
micro_agent/tools.py — ToolRegistry: 工具注册、查找、执行、schema 生成。

参考 MiniCode 的 ToolRegistry + ToolDefinition 设计。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List

from .messages import ToolResult


# ── ToolDefinition ────────────────────────────────────────────────────────────

@dataclass
class ToolDefinition:
    name: str
    description: str
    func: Callable[..., str]
    parameters: Dict[str, Any] = field(default_factory=dict)
    # parameters 格式：{"properties": {参数 schema}, "required": [必填参数列表]}

    def to_openai_schema(self) -> Dict[str, Any]:
        """生成 OpenAI function-calling 格式的 tool schema。"""
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


# ── ToolRegistry ──────────────────────────────────────────────────────────────

class ToolRegistry:
    """管理所有工具的注册、查找和统一执行。"""

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}

    # ── 注册 ──────────────────────────────────────────────────────────────

    def register(self, tool: ToolDefinition) -> None:
        """注册一个工具。同名工具会被覆盖。"""
        self._tools[tool.name] = tool

    def register_many(self, tools: List[ToolDefinition]) -> None:
        """批量注册。"""
        for t in tools:
            self.register(t)

    # ── 查找 ──────────────────────────────────────────────────────────────

    def find(self, name: str) -> ToolDefinition | None:
        """按名查找工具，未找到返回 None。"""
        return self._tools.get(name)

    def list_names(self) -> List[str]:
        """返回所有已注册工具的名称列表。"""
        return list(self._tools.keys())

    # ── Schema ─────────────────────────────────────────────────────────────

    def to_openai_schema(self) -> List[Dict[str, Any]]:
        """生成发给 DeepSeek/OpenAI API 的 tools 数组。"""
        return [t.to_openai_schema() for t in self._tools.values()]

    # ── 执行 ──────────────────────────────────────────────────────────────

    def execute(self, name: str, args: Dict[str, Any]) -> ToolResult:
        """
        统一执行入口。

        - 未知工具 → ToolResult(is_error=True)
        - 正常执行 → ToolResult(content=func(**args))
        - 函数抛异常 → ToolResult(is_error=True, content=错误信息)
        """
        tool = self._tools.get(name)
        if tool is None:
            return ToolResult(
                tool_use_id="unknown",
                tool_name=name,
                content=f"Unknown tool '{name}'. Available: {self.list_names()}",
                is_error=True,
            )

        try:
            result_str = tool.func(**args)
            return ToolResult(
                tool_use_id="",  # 由调用方填入
                tool_name=name,
                content=result_str,
                is_error=False,
            )
        except TypeError as e:
            return ToolResult(
                tool_use_id="",
                tool_name=name,
                content=f"Wrong params for '{name}': {e}. "
                        f"Expected: {json.dumps(tool.parameters, ensure_ascii=False)}",
                is_error=True,
            )
        except Exception as e:
            return ToolResult(
                tool_use_id="",
                tool_name=name,
                content=f"Tool '{name}' threw an error: {e}",
                is_error=True,
            )

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools
