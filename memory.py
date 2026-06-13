"""
micro_agent/memory.py — 自动发现和加载项目指令文件。

搜索 MINI.md / CLAUDE.md，合并为 system prompt 的记忆段落。
"""

import os

# ── 搜索路径定义 ──────────────────────────────────────────────────────────────

# 项目级候选文件
PROJECT_CANDIDATES = [
    "MINI.md",
    "CLAUDE.md",
    ".mini-code/MINI.md",
    ".claude/CLAUDE.md",
    ".claude/MINI.md",
]

# 用户全局候选文件
HOME = os.path.expanduser("~")
GLOBAL_CANDIDATES = [
    os.path.join(HOME, "MINI.md"),
    os.path.join(HOME, "CLAUDE.md"),
]

MAX_PER_FILE = 4000
MAX_TOTAL = 8000


# ── 文件读取 ─────────────────────────────────────────────────────────────────

def _read_file(path: str) -> str | None:
    """读取文件内容。不存在或为空返回 None。"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            return content if content else None
    except (FileNotFoundError, PermissionError, IsADirectoryError):
        return None


def _truncate(text: str, limit: int) -> str:
    """截断文本到 limit 字符，末尾说明实际长度。"""
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n\n[truncated, original length: {len(text)} chars]"


# ── 主函数 ────────────────────────────────────────────────────────────────────

def load_memory(cwd: str) -> str:
    """加载所有可发现的指令文件，去重，合并返回。

    搜索顺序：
      1. 用户全局文件 (~/MINI.md, ~/CLAUDE.md)
      2. 项目根 → 逐级往上
    """
    discovered: list[tuple[str, str]] = []  # [(path, content)]
    seen_hashes: set[int] = set()
    remaining = MAX_TOTAL

    def _add(file_path: str, content: str) -> bool:
        nonlocal remaining
        h = hash(content)
        if h in seen_hashes:
            return False
        seen_hashes.add(h)
        truncated = _truncate(content, min(len(content), MAX_PER_FILE, remaining))
        discovered.append((file_path, truncated))
        remaining -= len(truncated)
        return remaining > 0

    # 1. 全局文件
    for candidate in GLOBAL_CANDIDATES:
        content = _read_file(candidate)
        if content and not _add(candidate, content):
            break

    # 2. 项目根和逐级目录
    if remaining > 0:
        path = os.path.abspath(cwd)
        dirs_to_check: list[str] = []
        while True:
            dirs_to_check.append(path)
            parent = os.path.dirname(path)
            if parent == path:
                break
            path = parent
        dirs_to_check.reverse()  # 从根到 cwd

        for d in dirs_to_check:
            for name in PROJECT_CANDIDATES:
                candidate = os.path.join(d, name)
                content = _read_file(candidate)
                if content and not _add(candidate, content):
                    break
            if remaining <= 0:
                break

    # 3. 拼接
    if not discovered:
        return ""

    sections = ["# Project Instructions"]
    for file_path, content in discovered:
        rel_path = os.path.relpath(file_path, cwd) if os.path.isabs(file_path) else file_path
        sections.append(f"## {rel_path}\n\n{content}")

    return "\n\n".join(sections)
