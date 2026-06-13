# micro_agent/compact/microcompact.py
"""Tier 1: 微压缩 — 删除未完成的工具调用（有 tool_call 无结果）"""

from ..messages import ChatMessage, AssistantToolCall, ToolResult


def microcompact(messages: list[ChatMessage]) -> list[ChatMessage]:
    """
    删除末尾的孤儿 tool_calls（模型调用了但还没拿到结果）。
    这些 orphaned calls 没有对应的 ToolResult，扔给下一轮 API 会出错。
    """
    if not messages:
        return messages

    # Strip trailing AssistantToolCall entries
    while messages and isinstance(messages[-1], AssistantToolCall):
        messages = messages[:-1]

    return messages
