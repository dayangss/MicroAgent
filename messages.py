"""
micro_agent/messages.py — 6 种消息类型 + OpenAI 线格式转换。

MiniCode 消息类型（方案 B）：
  - SystemMessage : 系统提示词
  - UserMessage   : 用户输入 / 循环注入的提示
  - AssistantMessage : 模型文本输出（最终答案）
  - AssistantToolCall : 模型发起的工具调用（一个 call 一条消息）
  - ToolResult    : 工具执行结果
  - ContextSummary : 上下文压缩摘要（记忆系统接口）
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union


# ── 6 种消息类型 ──────────────────────────────────────────────────────────────

@dataclass
class SystemMessage:
    content: str

    @property
    def role(self) -> str:
        return "system"


@dataclass
class UserMessage:
    content: str

    @property
    def role(self) -> str:
        return "user"


@dataclass
class AssistantMessage:
    content: str      # 模型的文本回答

    @property
    def role(self) -> str:
        return "assistant"


@dataclass
class AssistantToolCall:
    tool_use_id: str   # 调用唯一 ID（OpenAI 生成的）
    tool_name: str      # 工具名
    input: Dict[str, Any]  # 工具参数

    @property
    def role(self) -> str:
        return "assistant_tool_call"


@dataclass
class ToolResult:
    tool_use_id: str    # 对应哪次调用
    tool_name: str      # 工具名（冗余，便于调试）
    content: str        # 工具返回文本
    is_error: bool = False  # 工具是否报错

    @property
    def role(self) -> str:
        return "tool_result"


@dataclass
class ContextSummary:
    content: str          # 压缩后的摘要文本
    compressed_count: int # 被压缩掉了多少条消息
    timestamp: float = field(default_factory=time.time)

    @property
    def role(self) -> str:
        return "context_summary"


# ── 联合类型 ──────────────────────────────────────────────────────────────────

ChatMessage = Union[
    SystemMessage,
    UserMessage,
    AssistantMessage,
    AssistantToolCall,
    ToolResult,
    ContextSummary,
]


# ── OpenAI 线格式转换 ─────────────────────────────────────────────────────────

def to_openai_format(messages: List[ChatMessage]) -> List[Dict[str, Any]]:
    """
    将内部消息列表转换为 OpenAI chat.completions.create 接受的 messages 格式。

    映射规则：
      - SystemMessage         → {"role": "system", "content": "..."}
      - UserMessage           → {"role": "user", "content": "..."}
      - AssistantMessage      → {"role": "assistant", "content": "..."}
      - AssistantToolCall     → {"role": "assistant", "content": None,
                                   "tool_calls": [...]}
        多个连续的 AssistantToolCall 会合并到一条 assistant 消息中
      - ToolResult            → {"role": "tool", "tool_call_id": "...",
                                   "content": "..."}
      - ContextSummary        → {"role": "user", "content": "..."}
                                 压缩摘要作为 user 消息注入
    """
    openai_msgs: List[Dict[str, Any]] = []
    i = 0

    while i < len(messages):
        msg = messages[i]

        if isinstance(msg, SystemMessage):
            openai_msgs.append({"role": "system", "content": msg.content})
            i += 1

        elif isinstance(msg, UserMessage):
            openai_msgs.append({"role": "user", "content": msg.content})
            i += 1

        elif isinstance(msg, AssistantMessage):
            openai_msgs.append({"role": "assistant", "content": msg.content})
            i += 1

        elif isinstance(msg, AssistantToolCall):
            # 收集连续的所有 AssistantToolCall，合并到一条 assistant 消息
            tool_calls = []
            while i < len(messages) and isinstance(messages[i], AssistantToolCall):
                tc = messages[i]
                tool_calls.append({
                    "id": tc.tool_use_id,
                    "type": "function",
                    "function": {
                        "name": tc.tool_name,
                        "arguments": json.dumps(tc.input, ensure_ascii=False),
                    },
                })
                i += 1
            openai_msgs.append({
                "role": "assistant",
                "content": None,
                "tool_calls": tool_calls,
            })

        elif isinstance(msg, ToolResult):
            openai_msgs.append({
                "role": "tool",
                "tool_call_id": msg.tool_use_id,
                "content": msg.content,
            })
            i += 1

        elif isinstance(msg, ContextSummary):
            # 压缩摘要作为 user 消息注入——告诉模型"之前发生了什么"
            openai_msgs.append({
                "role": "user",
                "content": f"[Context Summary]\n{msg.content}",
            })
            i += 1

        else:
            i += 1  # 未知类型，跳过

    return openai_msgs


# ── OpenAI 响应 → 内部消息 ────────────────────────────────────────────────────

def from_openai_response(
    response_message,  # openai.types.chat.ChatCompletionMessage
) -> List[ChatMessage]:
    """
    解析 OpenAI tool_calls 响应，生成 AssistantToolCall 列表。
    如果没有 tool_calls，返回一个 AssistantMessage。
    """
    if response_message.tool_calls:
        calls = []
        for tc in response_message.tool_calls:
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}
            calls.append(AssistantToolCall(
                tool_use_id=tc.id,
                tool_name=tc.funct