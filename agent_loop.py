"""
micro_agent/agent_loop.py — Agent 主循环。

依赖: messages + ToolRegistry + OpenAI SDK。
"""

from __future__ import annotations

import json
import time
from typing import List, Tuple

from openai import OpenAI

from .messages import (
    ChatMessage,
    SystemMessage,
    UserMessage,
    AssistantToolCall,
    ToolResult,
    from_openai_response,
    to_openai_format,
)
from .tools import ToolRegistry


# ── LLM 调用（含重试）────────────────────────────────────────────────────────

def _call_llm(
    client: OpenAI,
    model: str,
    messages: List[ChatMessage],
    registry: ToolRegistry,
    max_retries: int = 3,
) -> list[ChatMessage]:
    """调 LLM，带指数退避重试。返回内部消息列表。"""
    for attempt in range(max_retries):
        try:
            r = client.chat.completions.create(
                model=model,
                messages=to_openai_format(messages),
                tools=registry.to_openai_schema() or None,
            )
            return from_openai_response(r.choices[0].message)
        except Exception as e:
            status = getattr(e, "status_code", None) or getattr(
                getattr(e, "response", None), "status_code", None
            )
            retryable = status is not None and (status == 429 or status >= 500)
            if not retryable or attempt == max_retries - 1:
                raise
            wait = 2 ** attempt
            print(f"  [Retry] {status}, waiting {wait}s")
            time.sleep(wait)
    return []  # unreachable


# ── Agent 主循环 ─────────────────────────────────────────────────────────────

def run(
    prompt: str,
    registry: ToolRegistry,
    client: OpenAI,
    model: str = "deepseek-chat",
    system_prompt: str = "",
    max_steps: int = 12,
    timeout: float = 120.0,
) -> Tuple[str, List[ChatMessage]]:
    """
    执行 agent 循环。

    参数:
      prompt: 用户输入
      registry: 已注册工具的 ToolRegistry
      client: OpenAI 客户端（已配置 base_url + api_key）
      model: 模型名
      system_prompt: 系统提示词（可选）
      max_steps: 最大步数
      timeout: 超时（秒）

    返回:
      (最终答案文本, 完整消息历史)
    """
    # 初始化消息列表
    messages: List[ChatMessage] = []
    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))
    messages.append(UserMessage(content=prompt))

    t0 = time.time()
    tool_history: List[Tuple[str, str]] = []  # (name, args_json) 循环检测

    for step in range(1, max_steps + 1):
        # 超时检查
        if time.time() - t0 > timeout:
            messages.append(UserMessage(content="[Agent] Timeout."))
            return "[Agent] Timeout.", messages

        # 调用 LLM
        try:
            new_msgs = _call_llm(client, model, messages, registry)
        except Exception as e:
            err_msg = f"[Agent] API error: {e}"
            messages.append(UserMessage(content=err_msg))
            return err_msg, messages

        if not new_msgs:
            # 空响应
            if step < max_steps:
                messages.append(UserMessage(
                    content="Your last response was empty after tool results. "
                            "Continue with the next step."
                ))
                continue
            return "[Agent] Empty response.", messages

        # 处理每条新消息
        has_tool_call = False
        for msg in new_msgs:
            messages.append(msg)

            if isinstance(msg, AssistantToolCall):
                has_tool_call = True

                # 执行工具
                result: ToolResult = registry.execute(msg.tool_name, msg.input)
                result.tool_use_id = msg.tool_use_id  # 填入 ID
                messages.append(result)

                print(f"  [Step {step}] {msg.tool_name}"
                      f"({json.dumps(msg.input, ensure_ascii=False)})"
                      f" → {'✓' if not result.is_error else '✗'}")

                # 循环检测
                tool_history.append((msg.tool_name, json.dumps(msg.input, sort_keys=True)))
                if len(tool_history) >= 3 and len(set(tool_history[-3:])) == 1:
                    messages.append(UserMessage(
                        content="Same tool+args 3x in a row. Try a different approach."
                    ))
                    tool_history.clear()

        # 如果没有工具调用，最后一条 AssistantMessage 就是答案
        if not has_tool_call and new_msgs:
            last = new_msgs[-1]
            return getattr(last, "content", "[Agent] Done."), messages

    return "[Agent] Max steps reached.", messages
