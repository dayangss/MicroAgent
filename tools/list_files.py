# micro_agent/tools/list_files.py
"""list_files — 列出目录中的文件和子目录。"""

import os


def list_files(path: str = ".") -> str:
    try:
        entries = sorted(os.listdir(path))[:200]
        lines = [("dir  " if os.path.isdir(os.path.join(path, e)) else "file ") + e for e in entries]
        return "\n".join(lines) or "(empty)"
    except Exception as e:
        return f"List error: {e}"
