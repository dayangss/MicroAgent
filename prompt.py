"""micro_agent/prompt.py — Build system prompt from registry, cwd, and memory."""

from .tools import ToolRegistry


def build_system_prompt(cwd: str, registry: ToolRegistry, memory: str = "") -> str:
    parts = [
        "You are a terminal coding assistant (MicroAgent).",
        "Inspect repos, use tools, make code changes, explain results.",
        f"Current working directory: {cwd}",
        "",
    ]

    names = registry.list_names()
    if names:
        bullet = "\n".join(f"  - {n}" for n in names)
        parts.append(f"Available tools ({len(names)}):\n{bullet}")
        parts.append("Use tools to inspect, search, read, write, and run code.")
    else:
        parts.append("No tools available. Answer from knowledge only.")
    parts.append("")

    parts.extend([
        "Behavior rules:",
        "- Still working -> start with <progress>. Continue next step.",
        "- Done -> start with <final> and give the answer.",
        "- Need input -> use ask_user tool, not text.",
        "- Keep changes minimal, practical, working-oriented.",
        "- Asked to build/modify -> DO THE WORK. Don't stop at a plan.",
        "- Don't make subjective choices unless explicitly asked.",
        "",
    ])

    if memory:
        parts.append(f"Additional context:\n{memory}\n")

    return "\n".join(parts)
