# micro_agent/compact/auto_compact.py
"""Tier 2: 自动压缩 — 消息太多时调用 LLM 生成摘要。"""

from messages import ChatMessage, ContextSummary, SystemMessage, UserMessage


def estimate_tokens(messages: list[ChatMessage]) -> int:
    """粗略 token 估算：4 字符 ≈ 1 token。"""
    total = 0
    for m in messages:
        text = getattr(m, "content", "")
        if text:
            total += len(text) // 4 + 1
    return total


def auto_compact(
    messages: list[ChatMessage],
    max_tokens: int = 8000,
) -> tuple[list[ChatMessage], ContextSummary | None]:
    """
    当预估 token 超过 max_tokens 时，生成上下文摘要。
    返回 (新消息列表, 摘要对象或 None)。
    注意：实际 LLM 调用由调用方注入（解耦 DeepSeek 依赖）。
    """
    tokens = estimate_tokens(messages)
    if tokens <= max_tokens:
        return messages, None

    # 简单策略：取前半部分做摘要，保留最近的消息
    split = max(len(messages) // 3, 10)
    old = messages[:split]
    recent = messages[split:]

    # 生成摘要（不调 LLM，用规则摘要）—— LLM 版本由调用方实现
    parts = []
    for m in old:
        text = getattr(m, "content", "")
        if text and len(text) > 30:
            parts.append(f"[{getattr(m, 'role', '?')}] {text[:80]}...")
        elif text:
            parts.append(f"[{getattr(m, 'role', '?')}] {text}")

    summary_text = "Earlier conversation:\n" + "\n".join(parts[:20])
    summary = ContextSummary(
        content=summary_text,
        compressed_count=len(old),
    )

    return recent, summary
