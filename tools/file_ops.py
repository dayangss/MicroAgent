# micro_agent/tools/file_ops.py
"""read_file / write_file / list_directory — 文件系统操作。"""

import os


def read_file(path: str) -> str:
    try:
        with open(path) as f: return f.read()
    except FileNotFoundError: return f"'{path}' not found."
    except Exception as e: return f"Read error: {e}"


def write_file(path: str, content: str) -> str:
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path,"w") as f: f.write(content)
        return f"Wrote {len(content)} bytes to {path}."
    except Exception as e: return f"Write error: {e}"


def list_directory(path: str = ".") -> str:
    try:
        items = sorted(os.listdir(path))
        return "\n".join(items) or "(empty)"
    except Exception as e: return f"List error: {e}"
