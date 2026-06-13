# micro_agent/compact/snip_compact.py
"""Tier 3: 快照压缩 — 移除中间的工具互动对，保留首尾。"""

from messages import ChatMessage, AssistantToolCall, ToolResult, SnipBoundary


def snip_compact(messages: list[ChatMessage], max_messages: int = 30) -> tuple[list[ChatMessage], SnipBoundary | None]:
    """当消息数 > max_messages 时，从中间截断工具交互对（tool_call + tool_result），保留头和尾。"""
    if len(messages) <= max_messages:
        return messages, None

    # Find system + early user messages → keep
    # Find last ~10 messages → keep
    keep_head = 5   # system + first user interaction
    keep_tail = 10  # last tool interactions + final answer
    total = len(messages)
    if total <= keep_head + keep_tail:
        return messages, None

    removed_ids = []
    removed_count = total - keep_head - keep_tail
    kept = messages[:keep_head] + messages[total - keep_tail:]

    boundary = SnipBoundary(
        content=f"[SnipCompact] Removed {removed_count} middle messages, kept {len(kept)}.",
        removed_message_ids=removed_ids,
        removed_count=removed_count,
    )

    return kept, boundary
