"""micro_agent/tools/load_skill.py — Load skill content by name.

Aligned with MiniCode src/tools/load-skill.ts.
"""

from ..skills import load_skill


def _create_load_skill_tool(cwd: str):
    """Returns a ToolDefinition-compatible callable for load_skill."""
    def _load_skill(name: str) -> str:
        skill = load_skill(cwd, name)
        if not skill:
            return f"Unknown skill: {name}"
        return '\n'.join([
            f"SKILL: {skill.name}",
            f"SOURCE: {skill.source}",
            f"PATH: {skill.path}",
            '',
            skill.content,
        ])

    return _load_skill
