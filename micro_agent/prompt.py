"""micro_agent/prompt.py — Build system prompt from registry, cwd, memory, and skills.

Aligned with MiniCode src/prompt.ts.
"""

from __future__ import annotations

from .tool_registry import ToolRegistry
from .skills import SkillSummary
from typing import List


def build_system_prompt(cwd: str, registry: ToolRegistry, memory: str = "",
                        skills: List[SkillSummary] | None = None) -> str:
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
        "- If the user names a skill or clearly asks for a workflow that matches a listed skill, call load_skill before following it.",
        "",
    ])

    # Skills section
    skill_list = skills if skills is not None else registry.get_skills()
    if skill_list:
        parts.append(
            f"Available skills:\n" +
            "\n".join(f"- {s.name}: {s.description}" for s in skill_list)
        )
    else:
        parts.append("Available skills:\n- none discovered")
    parts.append("")

    if memory:
        parts.append(f"Additional context:\n{memory}\n")
    return "\n".join(parts)
