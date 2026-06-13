"""micro_agent/skills.py — Skill discovery, loading, install, and removal.

Aligned with MiniCode src/skills.ts.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List


@dataclass
class SkillSummary:
    name: str
    description: str
    path: str
    source: str  # 'project' | 'user' | 'compat_project' | 'compat_user'


@dataclass
class LoadedSkill(SkillSummary):
    content: str


def _extract_description(markdown: str) -> str:
    """Extract the first non-header paragraph line from SKILL.md content."""
    normalized = markdown.replace('\r\n', '\n')
    blocks = [b.strip() for b in normalized.split('\n\n') if b.strip()]

    for block in blocks:
        if block.startswith('#'):
            continue
        lines = block.split('\n')
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                return stripped.replace('`', '')

    return 'No description provided.'


def _get_skill_roots(cwd: str) -> list[tuple[str, str]]:
    """Return (root_path, source_label) in priority order."""
    home = os.path.expanduser('~')
    return [
        (os.path.join(home, '.micro_agent', 'skills'), 'user'),
        (os.path.join(cwd, '.mini-code', 'skills'), 'project'),
        (os.path.join(cwd, '.claude', 'skills'), 'compat_project'),
        (os.path.join(home, '.claude', 'skills'), 'compat_user'),
    ]


def _list_skill_dirs(root: str, source: str) -> list[LoadedSkill]:
    """Scan a skill root directory for SKILL.md files."""
    results: list[LoadedSkill] = []
    try:
        entries = os.scandir(root)
    except (FileNotFoundError, NotADirectoryError, PermissionError):
        return results

    with entries:
        for entry in entries:
            if not entry.is_dir():
                continue
            skill_path = os.path.join(root, entry.name, 'SKILL.md')
            try:
                with open(skill_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except (FileNotFoundError, PermissionError, IsADirectoryError):
                continue

            results.append(LoadedSkill(
                name=entry.name,
                description=_extract_description(content),
                path=skill_path,
                source=source,
                content=content,
            ))

    return results


def discover_skills(cwd: str) -> list[SkillSummary]:
    """Discover all skills from user and project directories.

    First-found wins: skills are deduplicated by name, with priority:
    user > project > compat_project > compat_user.
    """
    by_name: dict[str, LoadedSkill] = {}

    for root, source in _get_skill_roots(cwd):
        for skill in _list_skill_dirs(root, source):
            if skill.name not in by_name:
                by_name[skill.name] = skill

    return [
        SkillSummary(name=s.name, description=s.description, path=s.path, source=s.source)
        for s in by_name.values()
    ]


def load_skill(cwd: str, name: str) -> LoadedSkill | None:
    """Load a specific skill's full content by name."""
    normalized = name.strip()
    if not normalized:
        return None

    for root, source in _get_skill_roots(cwd):
        skill_path = os.path.join(root, normalized, 'SKILL.md')
        try:
            with open(skill_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return LoadedSkill(
                name=normalized,
                description=_extract_description(content),
                path=skill_path,
                source=source,
                content=content,
            )
        except (FileNotFoundError, PermissionError, IsADirectoryError):
            continue

    return None
