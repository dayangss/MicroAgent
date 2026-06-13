"""micro_agent/messages.py — 8 种消息类型 + OpenAI 线格式转换。

MiniCode 对齐（方案 B+）：
  SystemMessage / UserMessage / AssistantMessage / AssistantToolCall
  ToolResult / ContextSummary / AssistantProgress / SnipBoundary
"""

from __future__ import annotations
import json, time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Union


# ── 8 种消息类型 ────────────────────────────────────────────────────────

@dataclass
class SystemMessage:
    content: str
    @property
    def role(self) -> str: return "system"

@dataclass
class UserMessage:
    content: str
    @property
    def role(self) -> str: return "user"

@dataclass
class AssistantMessage:
    content: str
    @property
    def role(self) -> str: return "assistant"

@dataclass
class AssistantToolCall:
    tool_use_id: str
    tool_name: str
    input: Dict[str, Any]
    @property
    def role(self) -> str: return "assistant_tool_call"

@dataclass
class ToolResult:
    tool_use_id: str
    tool_name: str
    content: str
    is_error: bool = False
    @property
    def role(self) -> str: return "tool_result"

@dataclass
class ContextSummary:
    content: str
    compressed_count: int
    timestamp: float = field(default_factory=time.time)
    @property
    def role(self) -> str: return "context_summary"

@dataclass
class AssistantProgress:
    """模型发送的进度更新——还有后续步骤，不是最终答案。"""
    content: str
    @property
    def role(self) -> str: return "assistant_progress"

@dataclass
class SnipBoundary:
    """快照压缩边界——记录被移除的消息范围。"""
    content: str
    removed_message_ids: List[str] = field(default_factory=list)
    removed_count: int = 0
    tokens_freed: int = 0
    timestamp: float = field(default_factory=time.time)
    @property
    def role(self) -> str: return "snip_boundary"


ChatMessage = Union[
    SystemMessage, UserMessage, AssistantMessage, AssistantToolCall,
    ToolResult, ContextSummary, AssistantProgress, SnipBoundary,
]


# ── OpenAI 线格式转换 ───────────────────────────────────────────────────

def to_openai_format(messages: List[ChatMessage]) -> List[Dict[str, Any]]:
    openai_msgs = []
    i = 0
    while i < len(messages):
        msg = messages[i]
        if isinstance(msg, (SystemMessage, UserMessage, AssistantMessage, AssistantProgress)):
            openai_msgs.append({"role": "assistant" if isinstance(msg, AssistantProgress) else msg.role, "content": msg.content})
            i += 1
        elif isinstance(msg, AssistantToolCall):
            tool_calls = []
            while i < len(messages) and isinstance(messages[i], AssistantToolCall):
                tc = messages[i]
                tool_calls.append({"id": tc.tool_use_id, "type": "function",
                    "function": {"name": tc.tool_name, "arguments": json.dumps(tc.input, ensure_ascii=False)}})
                i += 1
            openai_msgs.append({"role": "assistant", "content": None, "tool_calls": tool_calls})
        elif isinstance(msg, ToolResult):
            openai_msgs.append({"role": "tool", "tool_call_id": msg.tool_use_id, "content": msg.content})
            i += 1
        elif isinstance(msg, (ContextSummary, SnipBoundary)):
            openai_msgs.append({"role": "user", "content": f"[{msg.role}]\n{msg.content}"})
            i += 1
        else:
            i += 1
    return openai_msgs


def from_openai_response(response_message) -> List[ChatMessage]:
    if response_message.tool_calls:
        return [AssistantToolCall(tool_use_id=tc.id, tool_name=tc.function.name,
            input=json.loads(tc.function.arguments) if tc.function.arguments else {})
            for tc in response_message.tool_calls]
    if response_message.content:
        content = response_message.content.strip()
        # Progress detection
        if content.startswith("<progress>"):
            return [AssistantProgress(content=content)]
        return [AssistantMessage(content=content)]
    return []
