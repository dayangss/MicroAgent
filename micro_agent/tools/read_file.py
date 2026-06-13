# micro_agent/tools/read_file.py
"""read_file — 读取文件，支持 offset/limit 分块。"""

import os

DEFAULT_LIMIT = 8000
MAX_LIMIT = 20000


def read_file(path: str, offset: int = 0, limit: int = DEFAULT_LIMIT) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        limit = min(MAX_LIMIT, limit)
        end = min(len(content), offset + limit)
        chunk = content[offset:end]
        header = (
            f"FILE: {path}\n"
            f"OFFSET: {offset}\n"
            f"END: {end}\n"
            f"TOTAL_CHARS: {len(content)}\n"
            f"TRUNCATED: {'yes — call read_file again with offset ' + str(end) if end < len(content) else 'no'}\n\n"
        )
        return header + chunk
    except FileNotFoundError:
        return f"'{path}' not found."
    except Exception as e:
        return f"Read error: {e}"
