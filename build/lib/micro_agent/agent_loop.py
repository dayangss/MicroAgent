"""micro_agent/agent_loop.py — Agent main loop."""

from __future__ import annotations

import json, time
from typing import List, Tuple

from openai import OpenAI

from .messages import (
    ChatMessage, SystemMessage, UserMessage, AssistantToolCall,
    ToolResult, from_openai_response, to_openai_format,
)
from .tool_registry import ToolRegistry


def _call_llm(client, model, messages, registry, max_retries=3):
    for attempt in range(max_retries):
        try:
            r = client.chat.completions.create(
                model=model, messages=to_openai_format(messages),
                tools=registry.to_openai_schema() or None)
            return from_openai_response(r.choices[0].message)
        except Exception as e:
            status = getattr(e, "status_code", None) or getattr(
                getattr(e, "response", None), "status_code", None)
            retryable = status is not None and (status == 429 or status >= 500)
            if not retryable or attempt == max_retries - 1:
                raise
            wait = 2 ** attempt
            print(f"  [Retry] {status}, waiting {wait}s")
            time.sleep(wait)
    return []


def run(prompt, registry, client, model="deepseek-chat",
        system_prompt="", max_steps=12, timeout=120.0):
    messages = []
    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))
    messages.append(UserMessage(content=prompt))

    t0 = time.time()
    tool_history = []

    for step in range(1, max_steps + 1):
        if time.time() - t0 > timeout:
            return "[Agent] Timeout.", messages

        try:
            new_msgs = _call_llm(client, model, messages, registry)
        except Exception as e:
            err = f"[Agent] API error: {e}"
            return err, messages

        if not new_msgs:
            if step < max_steps:
                messages.append(UserMessage(
                    content="Your last response was empty. Continue with the next step."))
                continue
            return "[Agent] Empty response.", messages

        has_tool_call = False
        for msg in new_msgs:
            messages.append(msg)
            if isinstance(msg, AssistantToolCall):
                has_tool_call = True
                result = registry.execute(msg.tool_name, msg.input)
                result.tool_use_id = msg.tool_use_id
                messages.append(result)

                print(f"  [Step {step}] {msg.tool_name}"
                      f"({json.dumps(msg.input, ensure_ascii=False)})"
                      f" -> {'OK' if not result.is_error else 'ERR'}")

                tool_history.append((msg.tool_name, json.dumps(msg.input, sort_keys=True)))
                if len(tool_history) >= 3 and len(set(tool_history[-3:])) == 1:
                    messages.append(UserMessage(
                        content="Same tool+args 3x. Try a different approach."))
                    tool_history.clear()

        if not has_tool_call and new_msgs:
            last = new_msgs[-1]
            return getattr(last, "content", "[Agent] Done."), messages

    return "[Agent] Max steps reached.", messages
