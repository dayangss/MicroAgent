#!/usr/bin/env python3
"""micro_agent/main.py — MicroAgent entry point."""

import os, sys
from openai import OpenAI
from dotenv import load_dotenv
from .messages import ChatMessage
from .tool_registry import ToolDefinition, ToolRegistry
from .agent_loop import run as run_agent
from .prompt import build_system_prompt
from .memory import load_memory
from .tools import create_registry


def _ensure_env():
    candidates = [os.path.join(os.getcwd(), ".env")]
    _d = os.path.dirname(os.path.abspath(__file__))
    for i in range(4):
        candidates.append(os.path.join(_d, ".env"))
        candidates.append(os.path.join(_d, "agent_project", ".env"))
        _d = os.path.dirname(_d)
    candidates.append(os.path.join(os.path.expanduser("~"), ".micro_agent", ".env"))
    for f in candidates:
        if os.path.isfile(f) and os.path.getsize(f) > 0:
            load_dotenv(f)
            if os.getenv("DEEPSEEK_API_KEY"):
                return
    load_dotenv()


def create_agent(workspace: str | None = None):
    _ensure_env()
    key = os.getenv("DEEPSEEK_API_KEY")
    if not key:
        raise RuntimeError("DEEPSEEK_API_KEY not set")
    cwd = workspace or os.getcwd()
    client = OpenAI(api_key=key, base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"))
    registry = create_registry()
    memory = load_memory(cwd)
    system_prompt = build_system_prompt(cwd, registry, memory)
    return client, registry, system_prompt


def main():
    cwd = os.getcwd()
    client, registry, system_prompt = create_agent(cwd)
    print(f"MicroAgent v0.2.0 | {cwd} | {len(registry)} tools: {', '.join(registry.list_names())}")
    while True:
        try: user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt): print("\nBye."); break
        if not user_input: continue
        if user_input.lower() in ("exit","quit","/q"): print("Bye."); break
        answer, _ = run_agent(prompt=user_input, registry=registry, client=client, system_prompt=system_prompt)
        print(f"\n{answer}\n")


if __name__ == "__main__":
    main()
