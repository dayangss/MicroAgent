# micro_agent/compact/context_collapse.py
"""Tier 4: 上下文折叠 — 将冗长的工具结果压缩为简短摘要。"""

from messages import ChatMessage, ToolResult, ContextSummary, AssistantToolCall

MAX_TOOL_RESULT_LEN = 600


def context_collapse(messages: list[ChatMessage]) -> list[ChatMessage]:
    """截断超过 MAX_TOOL_RESULT_LEN 的工具结果。"""
    if not messages:
        return messages

    collapsed = []
    for msg in messages:
        if isinstance(msg, ToolResult) and len(msg.content) > MAX_TOOL_RESULT_LEN:
            summary = msg.content[:MAX_TOOL_RESULT_LEN] + f"\n... (collapsed from {len(msg.content)} chars)"
            collapsed.append(ToolResult(
                tool_use_id=msg.tool_use_id,
                tool_name=msg.tool_name,
                content=summary,
                is_error=msg.is_error,
            ))
        else:
            collapsed.append(msg)

    return collapsed
